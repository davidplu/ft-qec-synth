from dataclasses import dataclass, asdict

@dataclass
class Schedule:
    starts: list
    depth: int
    lower_bound: int
    efficiency: float
    def to_dict(self): return asdict(self)

def schedule(c):
    c.validate(); ready=[0]*c.num_qubits; finishes=[]; starts=[]; chains=[]; work=[0]*c.num_qubits
    for op in c.operations:
        t=max([ready[q] for q in op.qubits]+[finishes[d] for d in op.deps]+[0])
        duration=0 if op.gate=='BARRIER' else 1
        starts.append(t); finishes.append(t+duration)
        chains.append(duration+max([chains[d] for d in op.deps]+[0]))
        for q in op.qubits: ready[q]=t+duration; work[q]+=duration
    depth=max(finishes,default=0)
    two=sum(op.gate in ('CX','CZ','SWAP') for op in c.operations)
    conflict=(two+max(1,c.num_qubits//2)-1)//max(1,c.num_qubits//2)
    lower=max(max(work,default=0),max(chains,default=0),conflict)
    return Schedule(starts,depth,lower,lower/depth if depth else 1.)
