from dataclasses import dataclass, asdict
import json
from hashlib import sha256

@dataclass(frozen=True)
class Candidate:
    generating_basis: tuple
    orders: tuple
    flag_intervals: tuple
    check_order: tuple
    ancilla_assignment: tuple
    syndrome_budget: int
    parallelism: int

    def to_dict(self): return asdict(self)
    @property
    def id(self): return sha256(json.dumps(self.to_dict(),sort_keys=True).encode()).hexdigest()[:20]
    @classmethod
    def from_dict(cls,d):
        return cls(tuple(d['generating_basis']),tuple(tuple(x) for x in d['orders']),
                   tuple(tuple(tuple(y) for y in x) for x in d['flag_intervals']),
                   tuple(d['check_order']),tuple(d['ancilla_assignment']),d['syndrome_budget'],d['parallelism'])
    def validate(self,code):
        m=len(code.generators)
        if self.generating_basis!=tuple(map(str,code.generators)): raise ValueError('Basis mismatch')
        if len(self.orders)!=m or len(self.flag_intervals)!=m or len(self.ancilla_assignment)!=m: raise ValueError('Check count')
        if sorted(self.check_order)!=list(range(m)): raise ValueError('Check permutation')
        if not 1<=self.syndrome_budget<=max(1,m) or not 1<=self.parallelism<=self.syndrome_budget: raise ValueError('Ancilla budget')
        if any(a<0 or a>=self.syndrome_budget for a in self.ancilla_assignment): raise ValueError('Ancilla assignment')
        for p,order,intervals in zip(code.generators,self.orders,self.flag_intervals):
            if sorted(order)!=[q for q in range(code.n) if (p.x|p.z)>>q&1]: raise ValueError('Support permutation')
            if any(not 0<=lo<hi<=len(order) for lo,hi in intervals): raise ValueError('Flag interval')
