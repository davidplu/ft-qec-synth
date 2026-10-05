"""Safe suffix reuse for search; independent physical replay for final claims."""
from dataclasses import replace
from hashlib import sha256
import json, time
from ..faults.signatures import enumerate_faults, Signature
from ..faults.search import search_faults
from ..faults.verification import verify_witness
from ..faults.exclusion import verify_exclusion
from ..faults.analysis import analyze
from ..faults.spectrum import malignant_spectrum
from ..evaluation.resources import resources
from ..scheduling.scheduler import schedule
from .circuits import build_design, validate_ideal

METRICS = ('Q', 'D', 'QD', 'two_q_gates')


def classify(bounds, target):
    if bounds['lower_bound'] >= target: return 'VALID'
    if bounds.get('upper_bound') is not None and bounds['upper_bound'] < target: return 'INVALID'
    return 'UNKNOWN'


def fingerprint(c):
    return sha256(json.dumps(c.to_dict(), sort_keys=True).encode()).hexdigest()


class SignatureCache:
    """Reuse only a proven identical suffix with identical output coordinates.

    Non-idle repeated-memory circuits only. Changed detector maps, ancilla
    allocation or observable coordinates disable delta reuse. The new prefix
    is propagated afresh; fault locations are always enumerated afresh.
    """
    def __init__(self): self.entries = {}

    def get(self, c, parent=None):
        key = fingerprint(c)
        if key in self.entries:
            return self.entries[key]['signatures'], {'exact_cache': True, 'reused_suffix_operations': len(c.operations)}
        nd, nl = len(c.detectors), len(c.observables)
        names = sorted(o.record for o in c.operations if o.record and o.record.startswith('f'))
        nf = len(names); maps = {}
        for offset, rows in ((0,c.detectors),(nd,c.observables)):
            for i,row in enumerate(rows):
                for r in row: maps[r] = maps.get(r,0) ^ (1 << (offset+i))
        for i,name in enumerate(names): maps[name] = maps.get(name,0) ^ (1 << (nd+nl+i))
        xm = [(1 << q) << (nd+nl+nf) if q < c.code.n else 0 for q in range(c.num_qubits)]
        zm = [(1 << (c.code.n+q)) << (nd+nl+nf) if q < c.code.n else 0 for q in range(c.num_qubits)]
        suffix = [None]*(len(c.operations)+1); suffix[-1] = (xm.copy(),zm.copy())
        old = self.entries.get(parent); common = 0
        if old and old['maps'] == maps and old['coordinates'] == (c.num_qubits,c.code.n,nd,nl,nf):
            oldops = old['operations']
            # Metadata/deps do not affect error transfer. Physical qubits/gates/records do.
            def gatekey(op): return op.gate, op.qubits, op.record
            while common < min(len(oldops),len(c.operations)) and gatekey(oldops[-1-common]) == gatekey(c.operations[-1-common]):
                common += 1
            for k in range(common+1): suffix[len(c.operations)-k] = old['suffix'][len(oldops)-k]
            xm, zm = map(list, suffix[len(c.operations)-common])
        for i in range(len(c.operations)-common-1,-1,-1):
            op = c.operations[i]; g = op.gate; a = op.qubits[0] if op.qubits else 0
            if g in ('RESET','PREP'): xm[a] = zm[a] = 0
            elif g == 'M': xm[a] ^= maps.get(op.record,0)
            elif g == 'H': xm[a],zm[a] = zm[a],xm[a]
            elif g in ('S','SDG'): xm[a] ^= zm[a]
            elif g == 'CX':
                b = op.qubits[1]; xm[a] ^= xm[b]; zm[b] ^= zm[a]
            elif g == 'CZ':
                b = op.qubits[1]; xm[a] ^= zm[b]; xm[b] ^= zm[a]
            elif g == 'SWAP':
                b = op.qubits[1]; xm[a],xm[b] = xm[b],xm[a]; zm[a],zm[b] = zm[b],zm[a]
            suffix[i] = (xm.copy(),zm.copy())
        out = []
        for f in enumerate_faults(c,False):
            if f.kind == 'measurement': value = maps.get(c.operations[f.operation].record,0)
            else:
                xmap,zmap = suffix[f.operation+1]; value = 0
                for q,p in zip(f.qubits,f.label):
                    if p in 'XY': value ^= xmap[q]
                    if p in 'YZ': value ^= zmap[q]
            out.append(Signature(f,value & ((1 << nd)-1),(value >> (nd+nl)) & ((1 << nf)-1),
                                 (value >> nd) & ((1 << nl)-1),value >> (nd+nl+nf)))
        self.entries[key] = dict(signatures=out,suffix=suffix,maps=maps,operations=c.operations,
                                coordinates=(c.num_qubits,c.code.n,nd,nl,nf))
        return out, {'exact_cache': False, 'reused_suffix_operations': common,
                     'recomputed_prefix_operations': len(c.operations)-common,
                     'proof_condition': 'identical_physical_suffix_and_output_linear_maps'}


def attribution(c):
    s = schedule(c); groups = {}
    for i,op in enumerate(c.operations):
        if op.gate == 'BARRIER': continue
        key = f'round:{op.round_index}/check:{op.check}' if op.check is not None else 'terminal_readout' if op.round_index == c.experiment['rounds'] else 'input'
        g = groups.setdefault(key, {'qubits':set(), 'start':s.starts[i], 'end':0, 'two_q_gates':0,
                                     'measurements':0, 'resets':0, 'flag_operations':0})
        g['qubits'].update(op.qubits); g['end'] = max(g['end'], s.starts[i]+1)
        g['two_q_gates'] += op.gate in ('CX','CZ','SWAP')
        g['measurements'] += op.gate == 'M'; g['resets'] += op.gate == 'RESET'
        g['flag_operations'] += bool(op.role and ('flag' in op.role or 'verify' in op.role))
    for g in groups.values():
        g['Q_footprint'] = len(g['qubits']); g['qubits'] = sorted(g['qubits']); g['depth_span'] = g['end']-g['start']
    return {'components':groups, 'accounting':'2Q/measurement/reset counts are additive; Q footprints and depth spans overlap',
            'shared_ancillas':list(c.syndrome_qubits+c.flag_qubits),
            'reuse_dependency_edges':sum(len(op.deps) for op in c.operations),
            'extra_rounds': max(0,c.experiment['rounds']-3), 'unattributed_two_q_gates':0}


def evaluate(code, design, memory, target=3, cap=200000, cache=None, parent_hash=None):
    started = time.perf_counter(); c = build_design(code,design,memory)
    rec = {'architecture_id':design.id,'design':design.to_dict(),'candidate':design.candidate.to_dict(),
           'resources':resources(c),'circuit_hash':fingerprint(c),'attribution':attribution(c)}
    ideal = validate_ideal(c); rec['ideal_validation'] = ideal
    if not ideal['verified']:
        rec.update(bounds={'lower_bound':1,'upper_bound':None,'witness':None,'status':'INVALID_IDEAL_CIRCUIT'},
                   region='INVALID_STRUCTURE',malignant_spectrum=None,
                   runtime_seconds=time.perf_counter()-started)
        return rec,c
    cache = cache or SignatureCache(); ss,delta = cache.get(c,parent_hash)
    bounds = search_faults(c,ss,target-1,cap)
    rec.update(bounds=bounds,region=classify(bounds,target),delta_screen=delta)
    if bounds['witness']:
        audit = verify_witness(c.to_dict(),bounds['witness'])
        if not audit['verified']: raise ArithmeticError('Physical witness audit failed')
        rec['witness_verification'] = {'verified':True}
        rec['counterexample_analysis'] = analyze(c,bounds['witness'],ss).to_dict()
    # Spectrum only at the active failing tier, complete counts never inferred from caps.
    rec['malignant_spectrum'], _ = malignant_spectrum(c,ss,min(target-1,bounds['lower_bound']),cap)
    rec['runtime_seconds'] = time.perf_counter()-started
    return rec,c


def independent_audit(rec,circuit,target):
    if not validate_ideal(circuit)['verified']: return {'verified':False,'reason':'invalid_ideal_parity'}
    witness = rec['bounds'].get('witness')
    if witness and not verify_witness(circuit.to_dict(),witness)['verified']:
        return {'verified':False,'reason':'witness_replay'}
    through = min(target-1,rec['bounds']['lower_bound']-1)
    return verify_exclusion(circuit,through,False)
