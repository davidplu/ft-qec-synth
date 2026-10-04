import random
from .candidate import Candidate

def generate(code, count=32, seed=0):
    if count<1: raise ValueError('Positive candidate count required')
    rng=random.Random(seed); m=len(code.generators); seen=set()
    supports=[tuple(q for q in range(code.n) if (p.x|p.z)>>q&1) for p in code.generators]
    for attempt in range(max(1,count)*30):
        if len(seen)>=count: break
        orders=[list(s) for s in supports]
        check_order=list(range(m))
        if attempt:
            for o in orders: rng.shuffle(o)
            rng.shuffle(check_order)
        budget=1 if not attempt else rng.randint(1,max(1,m))
        intervals=[]
        for o in orders:
            nf=0 if not attempt or len(o)<2 else rng.randrange(3)
            choices=[(a,b) for a in range(len(o)) for b in range(a+1,len(o)+1)]
            intervals.append(tuple(rng.sample(choices,min(nf,len(choices)))))
        c=Candidate(tuple(map(str,code.generators)),tuple(map(tuple,orders)),tuple(intervals),tuple(check_order),
                    tuple(i%budget for i in range(m)),budget,rng.randint(1,budget))
        if c.id not in seen: seen.add(c.id); yield c
