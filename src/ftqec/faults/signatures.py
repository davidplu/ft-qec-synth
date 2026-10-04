from dataclasses import dataclass, asdict
from itertools import product
from ..codes.pauli import Pauli
from ..codes.logicals import logical_basis, logical_effect
from ..scheduling.scheduler import schedule
from .propagation import propagate
from ..serialization import json_native

@dataclass(frozen=True)
class Fault:
    operation: int
    qubits: tuple
    label: str
    kind: str
    location: str
    before: bool=False
    round_index: int | None = None
    check: int | None = None
    role: str | None = None
    interval: int | None = None
    interaction_position: int | None = None
    @classmethod
    def from_dict(cls, d):
        return cls(**{**d, "qubits": tuple(d["qubits"])})
    def pauli(self,n):
        return Pauli(n,sum(1<<q for q,p in zip(self.qubits,self.label) if p in 'XY'),
                     sum(1<<q for q,p in zip(self.qubits,self.label) if p in 'YZ'))
    def to_dict(self): return json_native(asdict(self))

@dataclass(frozen=True)
class Signature:
    fault: Fault
    detectors: int
    flags: int
    logical: int
    data: int

    @property
    def detection(self): return self.detectors # Flags are explicitly included in detectors.

def enumerate_faults(c,idles=False):
    for i,op in enumerate(c.operations):
        if op.gate=='BARRIER': continue
        metadata=dict(round_index=op.round_index,check=op.check,role=op.role,interval=op.interval,interaction_position=op.interaction_position)
        if op.gate=='M': yield Fault(i,op.qubits,'I','measurement',f'op:{i}',**metadata)
        else:
            for labels in product('IXYZ',repeat=len(op.qubits)):
                if all(p=='I' for p in labels): continue
                yield Fault(i,op.qubits,''.join(labels),'preparation' if op.role=='input_preparation_noise' else 'idle_gate' if op.gate=='IDLE' else op.gate.lower(),f'op:{i}',**metadata)
    if idles:
        s=schedule(c)
        spans={}
        for i,op in enumerate(c.operations):
            if op.role=='round_start': spans.setdefault(op.round_index,[s.starts[i],s.starts[i]])[0]=s.starts[i]
            if op.role=='round_end': spans.setdefault(op.round_index,[s.starts[i],s.starts[i]])[1]=s.starts[i]
        def idle_round(tick):
            return next((r for r,(lo,hi) in spans.items() if lo<=tick<hi),
                        -1 if spans and tick<min(lo for lo,hi in spans.values()) else c.experiment.get('rounds'))
        for q in range(c.num_qubits):
            uses=[(s.starts[i],i) for i,o in enumerate(c.operations) if q in o.qubits and o.gate!='BARRIER']
            previous=0
            for t,i in uses:
                for tick in range(previous,t):
                    for p in 'XYZ': yield Fault(i,(q,),p,'idle',f'idle:{q}:{tick}',True,round_index=idle_round(tick),role='idle')
                previous=t+1
            # Include trailing storage of every physical qubit through the end.
            for tick in range(previous,s.depth):
                for p in 'XYZ': yield Fault(len(c.operations),(q,),p,'idle',f'idle:{q}:{tick}',True,round_index=idle_round(tick),role='idle')

def signatures_forward(c,idles=False):
    c.validate(); pairs=logical_basis(c.code); out=[]
    for f in enumerate_faults(c,idles):
        if f.operation==len(c.operations):
            error=f.pauli(c.num_qubits)
            error=Pauli(c.code.n,error.x&((1<<c.code.n)-1),error.z&((1<<c.code.n)-1)); records={}
        else: error,records=propagate(c,f)
        bits=sum((sum(records.get(r,0) for r in d)&1)<<i for i,d in enumerate(c.detectors))
        if c.boundary_model=='ideal_initial_and_final_syndrome': bits |= c.code.syndrome(error)<<len(c.detectors)
        flags=sum(records.get(r,0)<<i for i,r in enumerate(sorted(r for r in records if r.startswith('f'))))
        logical=logical_effect(error,pairs) if c.boundary_model=='ideal_initial_and_final_syndrome' else 0
        offset=2*c.code.k if c.boundary_model=='ideal_initial_and_final_syndrome' else 0
        logical |= sum((sum(records.get(r,0) for r in d)&1)<<(offset+i) for i,d in enumerate(c.observables))
        out.append(Signature(f,bits,flags,logical,error.packed))
    return out


def signatures(c, idles=False, backend='suffix'):
    """Backward linear transfer maps; forward resimulation remains an oracle."""
    if backend == 'forward': return signatures_forward(c, idles)
    if backend != 'suffix': raise ValueError('Unknown signature backend')
    c.validate()
    legacy = c.boundary_model == 'ideal_initial_and_final_syndrome'
    pairs = logical_basis(c.code) if legacy else []
    nd = len(c.detectors) + (len(c.code.generators) if legacy else 0)
    nl = (2*c.code.k if legacy else 0) + len(c.observables)
    flag_names = sorted(op.record for op in c.operations if op.record and op.record.startswith('f'))
    nf = len(flag_names)
    record_maps = {}
    for i, detector in enumerate(c.detectors):
        for record in detector: record_maps[record] = record_maps.get(record, 0) ^ (1 << i)
    for i, obs in enumerate(c.observables):
        for record in obs: record_maps[record] = record_maps.get(record, 0) ^ (1 << (nd + (2*c.code.k if legacy else 0) + i))
    for i, name in enumerate(flag_names): record_maps[name] = record_maps.get(name, 0) ^ (1 << (nd+nl+i))
    xmap = [0]*c.num_qubits; zmap = [0]*c.num_qubits
    for q in range(c.code.n):
        for is_z, dest in [(False,xmap),(True,zmap)]:
            p=Pauli(c.code.n,0 if is_z else 1<<q,1<<q if is_z else 0)
            value=p.packed << (nd+nl+nf)
            if legacy: value |= (c.code.syndrome(p)<<len(c.detectors)) | (logical_effect(p,pairs)<<nd)
            dest[q]=value
    suffix=[None]*(len(c.operations)+1)
    suffix[-1]=(xmap.copy(),zmap.copy())
    for i in range(len(c.operations)-1,-1,-1):
        op=c.operations[i]; g=op.gate; a=op.qubits[0] if op.qubits else 0
        if g in ('RESET','PREP'): xmap[a]=zmap[a]=0
        elif g=='M': xmap[a]^=record_maps.get(op.record,0)
        elif g=='H': xmap[a],zmap[a]=zmap[a],xmap[a]
        elif g in ('S','SDG'): xmap[a]^=zmap[a]
        elif g=='CX':
            b=op.qubits[1]; xmap[a]^=xmap[b]; zmap[b]^=zmap[a]
        elif g=='CZ':
            b=op.qubits[1]; xmap[a]^=zmap[b]; xmap[b]^=zmap[a]
        elif g=='SWAP':
            b=op.qubits[1]; xmap[a],xmap[b]=xmap[b],xmap[a]; zmap[a],zmap[b]=zmap[b],zmap[a]
        suffix[i]=(xmap.copy(),zmap.copy())
    out=[]
    for fault in enumerate_faults(c,idles):
        if fault.kind=='measurement': value=record_maps.get(c.operations[fault.operation].record,0)
        else:
            index=fault.operation if fault.before else fault.operation+1
            if fault.operation==len(c.operations): index=fault.operation
            xm,zm=suffix[index]; value=0
            for q,p in zip(fault.qubits,fault.label):
                if p in 'XY': value^=xm[q]
                if p in 'YZ': value^=zm[q]
        out.append(Signature(fault,value&((1<<nd)-1),(value>>(nd+nl))&((1<<nf)-1),
                             (value>>nd)&((1<<nl)-1),value>>(nd+nl+nf)))
    return out
