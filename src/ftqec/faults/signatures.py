from dataclasses import dataclass, asdict
from itertools import product
from ..codes.pauli import Pauli
from ..codes.logicals import logical_basis, logical_effect
from ..scheduling.scheduler import schedule
from .propagation import propagate

@dataclass(frozen=True)
class Fault:
    operation: int
    qubits: tuple
    label: str
    kind: str
    location: str
    before: bool=False
    def pauli(self,n):
        return Pauli(n,sum(1<<q for q,p in zip(self.qubits,self.label) if p in 'XY'),
                     sum(1<<q for q,p in zip(self.qubits,self.label) if p in 'YZ'))
    def to_dict(self): return asdict(self)

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
        if op.gate=='M': yield Fault(i,op.qubits,'I','measurement',f'op:{i}')
        else:
            for labels in product('IXYZ',repeat=len(op.qubits)):
                if all(p=='I' for p in labels): continue
                yield Fault(i,op.qubits,''.join(labels),op.gate.lower(),f'op:{i}')
    if idles:
        s=schedule(c)
        for q in range(c.num_qubits):
            uses=[(s.starts[i],i) for i,o in enumerate(c.operations) if q in o.qubits and o.gate!='BARRIER']
            previous=0
            for t,i in uses:
                for tick in range(previous,t):
                    for p in 'XYZ': yield Fault(i,(q,),p,'idle',f'idle:{q}:{tick}',True)
                previous=t+1
            # Include trailing storage of every physical qubit through the end.
            for tick in range(previous,s.depth):
                for p in 'XYZ': yield Fault(len(c.operations),(q,),p,'idle',f'idle:{q}:{tick}',True)

def signatures(c,idles=False):
    c.validate(); pairs=logical_basis(c.code); out=[]
    for f in enumerate_faults(c,idles):
        if f.operation==len(c.operations):
            error=f.pauli(c.num_qubits)
            error=Pauli(c.code.n,error.x&((1<<c.code.n)-1),error.z&((1<<c.code.n)-1)); records={}
        else: error,records=propagate(c,f)
        bits=sum((sum(records.get(r,0) for r in d)&1)<<i for i,d in enumerate(c.detectors))
        bits |= c.code.syndrome(error)<<len(c.detectors)
        flags=sum(records.get(r,0)<<i for i,r in enumerate(sorted(r for r in records if r.startswith('f'))))
        logical=logical_effect(error,pairs)
        logical |= sum((sum(records.get(r,0) for r in d)&1)<<(2*c.code.k+i) for i,d in enumerate(c.observables))
        out.append(Signature(f,bits,flags,logical,error.packed))
    return out
