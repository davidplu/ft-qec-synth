"""Development-only constructions and independent terminal parity screening.

No held-out files, external architectures, or modifications of frozen runtime.
"""
from collections import Counter
from dataclasses import replace
from itertools import combinations
from pathlib import Path
import argparse
import gzip
import hashlib
import json
import time
import subprocess

from ftqec.codes.pauli import Pauli
from ftqec.codes.stabilizer import StabilizerCode
from ftqec.codes.symplectic import nullspace
from ftqec.certification.distance import exact_code_distance
from ftqec.architectures.generators import generate
from ftqec.circuits.memory import MemoryConfig, build_memory
from ftqec.faults.signatures import enumerate_faults, signatures
from ftqec.faults.batch_verification import singleton_effects
from ftqec.faults.verification import verify_witness
from ftqec.faults.search import witness
from ftqec.faults.analysis import analyze
from ftqec.faults.exclusion import verify_exclusion
from ftqec.search.malignant import MalignantConfig, run_malignant_search
from ftqec.search.cegis import SearchConfig, evaluate_memory

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'results/development_v2'
BENCH=ROOT/'benchmarks/development_v2'

def dump(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,indent=2,allow_nan=False)+'\n',encoding='utf-8')

def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()

def assert_frozen():
    f=json.loads((OUT/'algorithm_freeze.json').read_text())
    for group in ('source_hashes','previous_results_hashes'):
        for name,h in f[group].items():
            if sha(ROOT/name)!=h: raise AssertionError('Frozen file changed: '+name)
    return f['algorithm_commit']

def pauli(n,support,label):
    return ''.join(label if q in support else 'I' for q in range(n))

def shor(r,c):
    n=r*c
    return [pauli(n,{i*c+j,i*c+j+1},'Z') for i in range(r) for j in range(c-1)]+[
        pauli(n,set(range(i*c,(i+2)*c)),'X') for i in range(r-1)]

def grid(d):
    n=d*d; gs=[]
    for i in range(d-1):
        for j in range(d-1):
            gs.append(pauli(n,{i*d+j,i*d+j+1,(i+1)*d+j,(i+1)*d+j+1},'X' if (i+j)%2==0 else 'Z'))
    # Only commuting, independent boundary pairs enter the explicit construction.
    candidates=[]
    for i in range(d-1):
        candidates += [pauli(n,{i*d,(i+1)*d},'Z'),pauli(n,{i*d+d-1,(i+1)*d+d-1},'Z'),
                       pauli(n,{i,i+1},'X'),pauli(n,{(d-1)*d+i,(d-1)*d+i+1},'X')]
    for s in candidates:
        p=Pauli.parse(s); code=StabilizerCode.from_dict({'generators':gs})
        if all(not p.symplectic(g) for g in code.generators) and not code.is_stabilizer(p):gs.append(s)
    return gs

def direct_sum(a,b):return [g+'I'*len(b[0]) for g in a]+['I'*len(a[0])+g for g in b]

def mixed_generators(gs):
    # An invertible row-basis change, not a new code family.
    out=list(gs)
    for i,a in enumerate(gs):
        for j,b in enumerate(gs):
            if i!=j and ('X' in a and 'Z' in b):
                out[i]=str(Pauli.parse(a)^Pauli.parse(b));return out
    return out

def pool():
    assert_frozen(); rows=[]
    def add(name,gs,family,distance=None,parent=None):
        code=StabilizerCode.from_dict({'name':name,'generators':gs})
        proven=exact_code_distance(code,2000000) if code.n<=25 else {'status':'NOT_ENUMERATED'}
        if distance is not None:
            if proven.get('distance') is not None:assert proven['distance']==distance
            proven['construction_distance']=distance
        doc=code.to_dict();doc['provenance']={'method':'explicit generic construction in experiments/development_v2.py',
            'family':family,'shared_parent':parent,'external_architectures_used':False}
        dump(BENCH/'pool'/f'{name}.json',doc)
        rows.append({'name':name,'path':f'benchmarks/development_v2/pool/{name}.json',
                     'family':family,'shared_parent':parent,'distance_certificate':proven,'metrics':code.metrics(),
                     'css':all(not(p.x and p.z) for p in code.generators),'input_hash':code.input_hash})
        print(json.dumps({'generated':name,'n':code.n,'k':code.k,'distance':proven}),flush=True)
    steane=json.loads((ROOT/'benchmarks/development/steane.json').read_text())['generators']
    add('steane7',steane,'simplex_css',3)
    add('steane7_mixed',mixed_generators(steane),'simplex_css',3,'steane7')
    add('steane14_sum',direct_sum(steane,steane),'direct_sum',3,'two steane7 blocks')
    for r,c in ((3,3),(3,4),(3,5),(4,4),(4,5),(5,5)):
        add(f'shor{r}x{c}',shor(r,c),'rectangular_shor',min(r,c))
    add('shor3x3_mixed',mixed_generators(shor(3,3)),'rectangular_shor',3,'shor3x3')
    for d in (3,4,5):add(f'grid{d}',grid(d),'checkerboard_grid')
    h=[sum(1<<q for q in range(15) if (q+1)>>b&1) for b in range(4)]
    add('simplex15_k7',[str(Pauli(15,x,0)) for x in h]+[str(Pauli(15,0,z)) for z in h],'simplex_css',3)
    z=nullspace(h+[(1<<15)-1],15)
    add('affine15_k1',[str(Pauli(15,x,0)) for x in h]+[str(Pauli(15,0,v)) for v in z],'affine_css')
    for name in ('perfect5','noncss4'):
        d=json.loads((ROOT/f'benchmarks/development/{name}.json').read_text())
        add(name,d['generators'],'legacy_noncss')
    # Larger d>=7 candidate is not a held-out code; admission still needs calibration.
    add('shor7x7',shor(7,7),'rectangular_shor',7)
    dump(OUT/'candidate_pool.json',rows)

def terminal_ceiling(code,basis):
    c=build_memory(code,next(generate(code,1)),MemoryConfig(3,basis))
    faults=[f for f in enumerate_faults(c) if f.role in ('final_data_readout','final_basis_change')]
    effects=singleton_effects(c,faults)
    # Physical replay must demonstrate the single-final-record model for EVERY
    # terminal fault variant, including noisy basis changes.
    opindex={op.qubits[0]:i for i,op in enumerate(c.operations) if op.role=='final_data_readout'}
    units={}
    for f,(d,l) in zip(faults,effects):
        q=f.qubits[0]
        if f.kind=='measurement':units[q]=(f,d,l)
    assert len(units)==code.n
    for f,e in zip(faults,effects):assert e==(0,0) or e==units[f.qubits[0]][1:]
    examined=0;started=time.perf_counter()
    for w in range(1,code.n+1):
        for support in combinations(range(code.n),w):
            examined+=1
            if examined>2000000:
                return {'status':'UNRESOLVED','lower_bound':w,'upper_bound':None,'subsets':examined-1}
            d=l=0
            for q in support:d^=units[q][1];l^=units[q][2]
            if d==0 and l:
                group=[units[q][0] for q in support]
                ss=signatures(c);idx={(s.fault.location,s.fault.label):s for s in ss}
                obj=witness(c,[idx[f.location,f.label] for f in group]).to_dict()
                assert verify_witness(c,obj)['verified']
                return {'status':'EXACT_TERMINAL_ONLY','distance':w,'lower_bound':w,'upper_bound':w,
                    'witness':obj,'subsets':examined,'seconds':time.perf_counter()-started,
                    'method':'physical singleton replay plus exhaustive classical terminal-flip supports',
                    'full_circuit_lower_bound':False,'axes':c.experiment['readout_axes']}

def code_for(row):return StabilizerCode.from_dict(json.loads((ROOT/row['path']).read_text()))

def extend_pool():
    assert_frozen();rows=json.loads((OUT/'candidate_pool.json').read_text());parents={r['name']:r for r in rows}
    for name in ('grid3','grid4','grid5','shor4x4','affine15_k1'):
        parent=parents[name];code=code_for(parent);gs=list(map(str,code.generators))
        if name=='affine15_k1':new=mixed_generators(gs);suffix='_mixed'
        else:
            preceding={'X':Pauli(code.n),'Z':Pauli(code.n)};new=[];suffix='_dense'
            for g in code.generators:
                label='X' if g.x else 'Z'
                value=g^preceding[label];preceding[label]=value;new.append(str(value))
        child=StabilizerCode.from_dict({'name':name+suffix,'generators':new})
        assert child.rank==code.rank and all(code.is_stabilizer(p) for p in child.generators)
        doc=child.to_dict();doc['provenance']={'method':'invertible triangular check-basis transform in experiments/development_v2.py',
            'family':parent['family'],'shared_parent':name,'external_architectures_used':False}
        dump(BENCH/'pool'/f'{child.name}.json',doc)
        cert={**parent['distance_certificate'],'method':'rank-preserving stabilizer-group basis equivalence to '+name}
        row={'name':child.name,'path':f'benchmarks/development_v2/pool/{child.name}.json','family':parent['family'],
            'shared_parent':name,'distance_certificate':cert,'metrics':child.metrics(),
            'css':all(not(p.x and p.z) for p in child.generators),'input_hash':child.input_hash}
        if child.name not in {r['name'] for r in rows}:rows.append(row)
    dump(OUT/'candidate_pool.json',rows)
    # Correct a reporting label on saved calibration, without any recomputation
    # or change of the original prospective admission condition target<=3.
    for path in (OUT/'screen').glob('*.json'):
        s=json.loads(path.read_text())
        if s['classification']=='OPEN_HEADROOM' and s.get('d_initial',0)>=3:
            s['difficulty']='CERTIFICATION_TIER_LIMITED';dump(path,s)

def screen():
    assert_frozen();rows=json.loads((OUT/'candidate_pool.json').read_text());screened=[]
    for row in rows:
        code=code_for(row)
        for basis in ('X','Z'):
            path=OUT/'screen'/f"{row['name']}-{basis}.json"
            if path.exists():screened.append(json.loads(path.read_text()));continue
            boundary=terminal_ceiling(code,basis)
            item={'name':row['name'],'task':row['name']+'-'+basis,'basis':basis,'code_path':row['path'],
                  'family':row['family'],'shared_parent':row['shared_parent'],'n':code.n,'k':code.k,'css':row['css'],
                  'distance_certificate':row['distance_certificate'],'boundary':boundary}
            # Reject proven ceiling-one tasks without spending extraction search
            # time: every circuit already has trivial lower bound one.
            if boundary.get('distance')==1 or code.n>30:
                item.update(classification='BOUNDARY_LIMITED' if boundary.get('distance')==1 else 'COMPUTE_DEFERRED',
                            difficulty='UNREACHABLE/UNKNOWN',d_initial=1 if boundary.get('distance')==1 else None,
                            d_target=None,initial_target_frequency=None,calibration_runs=[])
            else:
                runs=[];mechanisms=Counter()
                for seed in (0,1,2):
                    run=run_malignant_search(code,MemoryConfig(3,basis),replace(MalignantConfig(),budget=6,seed=seed))
                    with gzip.open(OUT/'screen'/f"{item['task']}-seed{seed}.json.gz",'wt',encoding='utf-8') as f:json.dump(run,f,separators=(',',':'))
                    for r in run['records']:
                        c=build_memory(code,next(c for c in generate(code,6,seed) if c.id==r['architecture_id']),MemoryConfig(3,basis))
                        ss=signatures(c)
                        # Bounded deterministic diversity sample; coverage is
                        # observed, never an exhaustive absence claim.
                        classes=r['malignant_spectrum']['classes']
                        stride=max(1,len(classes)//64)
                        for cls in classes[::stride][:64]:
                            from ftqec.faults.spectrum import representative_witness
                            mechanisms.update(analyze(c,representative_witness(c,ss,cls),ss).failure_classes)
                    runs.append({'seed':seed,'initial_ids':run['initial_population_ids'],
                        'bounds':[r['bounds'] for r in run['records']],
                        'spectra':[r['malignant_spectrum']['layers'] for r in run['records']],
                        'seconds':run['runtime_seconds'],'best_dc':run['summary']['best_dc_lower_bound']})
                initial=max(r['best_dc'] for r in runs);target=initial+1
                cert=row['distance_certificate'];dcode=cert.get('construction_distance',cert.get('distance',cert.get('lower_bound',1)))
                classification='UNRESOLVED'
                if boundary.get('distance',0)<=initial and boundary.get('distance') is not None:classification='BOUNDARY_LIMITED'
                elif boundary.get('distance',0)>=target and dcode>=target:classification='OPEN_HEADROOM'
                difficulty=('USEFUL' if classification=='OPEN_HEADROOM' and target<=3 else
                            'CERTIFICATION_TIER_LIMITED' if classification=='OPEN_HEADROOM' and initial>=3 else
                            'TOO_EASY' if initial>=3 else 'UNREACHABLE/UNKNOWN')
                item.update(classification=classification,difficulty=difficulty,d_initial=initial,d_target=target,
                            initial_target_frequency=sum(r['best_dc']>=target for r in runs)/len(runs),
                            calibration_runs=runs,failure_mechanisms=dict(mechanisms),
                            mechanism_sample='up to 64 evenly spaced structural representatives per architecture')
            dump(path,item);screened.append(item);dump(OUT/'screening.json',screened)
            print(json.dumps({k:item.get(k) for k in ('task','classification','difficulty','d_initial','d_target')}),flush=True)
    dump(OUT/'screening.json',screened)

def pilot():
    assert_frozen();screened=json.loads((OUT/'screening.json').read_text());results=[]
    (OUT/'pilot').mkdir(exist_ok=True)
    # Admission never observes V0.3 outcomes. All eligible tasks receive the
    # same generic reachability vocabulary, including both interaction orders.
    for item in screened:
        if item['classification']!='OPEN_HEADROOM' or item['difficulty']!='USEFUL':continue
        path=OUT/'pilot'/f"{item['task']}.json"
        if path.exists():results.append(json.loads(path.read_text()));continue
        code=StabilizerCode.from_dict(json.loads((ROOT/item['code_path']).read_text()))
        mem=MemoryConfig(3,item['basis']);base=next(generate(code,1));construction=[]
        for flags in range(1,5):
            for reverse in (False,True):
                child=replace(base,flag_intervals=tuple(tuple((0,len(o)) for _ in range(flags)) for o in base.orders),
                    orders=tuple(tuple(reversed(o)) if reverse else o for o in base.orders),
                    syndrome_budget=len(base.orders),ancilla_assignment=tuple(range(len(base.orders))),parallelism=1)
                rec,c=evaluate_memory(code,child,mem,SearchConfig(target_dc=item['d_target'],decoder_weight=0))
                if rec['bounds']['lower_bound']>=item['d_target']:
                    rec['independent_exclusion']=verify_exclusion(c,item['d_target']-1)
                    assert rec['independent_exclusion']['verified']
                construction.append({'flags_per_check':flags,'reverse':reverse,**rec})
        generic=[]
        for seed in (6,7):
            initial=None
            for strategy in ('random','resource'):
                run=run_malignant_search(code,mem,replace(MalignantConfig(),budget=64,seed=seed,strategy=strategy,target_dc=item['d_target']))
                if initial is not None:assert initial==run['initial_population_ids']
                initial=run['initial_population_ids']
                f=OUT/'pilot'/f"{item['task']}-seed{seed}-{strategy}.json.gz"
                with gzip.open(f,'wt',encoding='utf-8') as stream:json.dump(run,stream,separators=(',',':'))
                generic.append({'seed':seed,'strategy':strategy,'file':f.relative_to(ROOT).as_posix(),
                                'summary':run['summary'],'seconds':run['runtime_seconds']})
        reached=any(c['bounds']['lower_bound']>=item['d_target'] for c in construction) or any(r['summary']['target_reached'] for r in generic)
        result={'task':item['task'],'target':item['d_target'],'reachable':reached,
                'status':'CONSTRUCTIVELY_REACHABLE' if reached else 'UNKNOWN_AFTER_BOUNDED_PILOT',
                'fixed_generic_constructions':construction,'matched_unguided_pilots':generic,'v03_pilot_runs':0}
        dump(path,result);results.append(result);dump(OUT/'pilots.json',results)
        print(json.dumps({'pilot':item['task'],'reachable':reached,'generic_successes':sum(r['summary']['target_reached'] for r in generic)}),flush=True)
    dump(OUT/'pilots.json',results)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('stage',choices=('pool','extend','screen','pilot'))
    args=parser.parse_args();(OUT/'screen').mkdir(parents=True,exist_ok=True)
    {'pool':pool,'extend':extend_pool,'screen':screen,'pilot':pilot}[args.stage]()
