"""Tiny dense-state oracle: actual states, measurements and ideal resets."""
import math, random
from ftqec.codes.pauli import Pauli

def apply_pauli(state,p):
    out=[0j]*len(state)
    for i,v in enumerate(state): out[i^p.x] = v * (1j**((p.x&p.z).bit_count())) * (-1)**((p.z&i).bit_count())
    return out

def dense_run(c,faults=(),seed=0):
    rng=random.Random(seed); n=c.num_qubits
    data=[complex(rng.random()-.5,rng.random()-.5) for _ in range(1<<c.code.n)]
    projectors=list(c.code.generators)
    if c.experiment.get('logical_pauli'): projectors.append(Pauli.parse(c.experiment['logical_pauli']))
    for p in projectors:
        transformed=apply_pauli(data,p); data=[a+b for a,b in zip(data,transformed)]
    norm=math.sqrt(sum(abs(a)**2 for a in data)); data=[a/norm for a in data]
    state=data+[0j]*((1<<n)-len(data)); records={}; events={}
    for f in faults: events.setdefault(f.operation,[]).append(f)
    def inject(f):
        nonlocal state
        p=Pauli(n,sum(1<<q for q,a in zip(f.qubits,f.label) if a in 'XY'),sum(1<<q for q,a in zip(f.qubits,f.label) if a in 'YZ'))
        state=apply_pauli(state,p)
    def measure(q):
        nonlocal state
        probability=sum(abs(v)**2 for i,v in enumerate(state) if i>>q&1)
        bit=int(rng.random()<probability)
        norm=math.sqrt(probability if bit else 1-probability)
        state=[v/norm if (i>>q&1)==bit else 0j for i,v in enumerate(state)]
        return bit
    for i,op in enumerate(c.operations):
        at=events.get(i,[])
        for f in at:
            if f.before: inject(f)
        a=op.qubits[0] if op.qubits else 0; g=op.gate
        if g=='H':
            new=state.copy()
            for col in range(len(state)):
                if col>>a&1: continue
                partner=col|(1<<a); new[col]=(state[col]+state[partner])/math.sqrt(2); new[partner]=(state[col]-state[partner])/math.sqrt(2)
            state=new
        elif g in ('S','SDG'):
            state=[v*((1j if g=='S' else -1j) if i>>a&1 else 1) for i,v in enumerate(state)]
        elif g in ('CX','CZ','SWAP'):
            new=[0j]*len(state); b=op.qubits[1]
            for col,v in enumerate(state):
                row=col; phase=1
                if g=='CX': row^=((col>>a)&1)<<b
                elif g=='CZ': phase=(-1)**((col>>a&1)*(col>>b&1))
                elif (col>>a&1)!=(col>>b&1): row^=(1<<a)|(1<<b)
                new[row]=v*phase
            state=new
        elif g in ('X','Y','Z'): inject(type('F',(),{'qubits':(a,),'label':g})())
        elif g in ('RESET','PREP'):
            if measure(a): inject(type('F',(),{'qubits':(a,),'label':'X'})())
        elif g=='M':
            bit=measure(a)
            if op.record: records[op.record]=bit^(sum(f.kind=='measurement' for f in at)&1)
        for f in at:
            if not f.before and f.kind!='measurement': inject(f)
    for f in events.get(len(c.operations),[]): inject(f)
    offsets=c.detector_offsets or [0]*len(c.detectors)
    detectors=sum(((sum(records[r] for r in d)&1)^offsets[i])<<i for i,d in enumerate(c.detectors))
    logical=sum((sum(records[r] for r in o)&1)<<i for i,o in enumerate(c.observables))
    flags=sum(records[r]<<i for i,r in enumerate(sorted(r for r in records if r.startswith('f'))))
    return detectors,logical,flags
