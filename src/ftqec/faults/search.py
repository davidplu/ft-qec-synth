from dataclasses import dataclass, asdict
from collections import defaultdict
from itertools import combinations
from ..codes.pauli import Pauli

@dataclass
class Counterexample:
    fault_count: int
    faults: list
    checks: list
    relation: str
    hook_support: list
    flags_fired: bool
    flag_information_cancelled: bool
    logical_coset: int
    detector_outcomes: int
    flag_outcomes: int
    final_data_pauli: str
    def to_dict(self): return asdict(self)

def witness(c,ss):
    detection=flags=logical=data=0
    for s in ss: detection^=s.detectors; flags^=s.flags; logical^=s.logical; data^=s.data
    p=Pauli.unpack(c.code.n,data)
    checks=sorted(set(c.operations[s.fault.operation].check for s in ss
                      if s.fault.operation<len(c.operations) and c.operations[s.fault.operation].check is not None))
    return Counterexample(len(ss),[s.fault.to_dict() for s in ss],checks,
        'same-check' if len(checks)==1 else 'cross-check' if len(checks)>1 else 'unassigned',
        [q for q in range(c.code.n) if (p.x|p.z)>>q&1],any(s.flags for s in ss),
        any(s.flags for s in ss) and flags==0,logical,detection,flags,str(p))

def search_faults(c,ss,max_weight=2,max_combinations=2000000):
    if max_weight not in range(1,7): raise ValueError('max_weight must be between 1 and 6')
    if max_combinations<0: raise ValueError('Negative work limit')
    examined=0; completed=0
    def result(found=None,reason=None):
        upper=found.fault_count if found else None; lower=completed+1
        status=('EXACT' if upper==lower else 'UPPER_BOUND') if upper else ('LOWER_BOUND' if completed else 'UNRESOLVED')
        return dict(status=status,lower_bound=lower,upper_bound=upper,excluded_through=completed,
                    witness=found.to_dict() if found else None,reason=reason,combinations_examined=examined,
                    fault_locations=len(set(s.fault.location for s in ss)),fault_variants=len(ss),requested_weight=max_weight)
    for s in ss:
        if examined>=max_combinations: return result(reason='work_limit')
        examined+=1
        if not s.detection and s.logical: return result(witness(c,[s]))
    completed=1
    if max_weight==1: return result()
    groups=defaultdict(list)
    for i,s in enumerate(ss): groups[s.detection].append(i)
    # Only equal detector signatures can cancel in a pair.
    for group in groups.values():
        for offset,i in enumerate(group):
            for j in group[offset+1:]:
                if ss[i].fault.location==ss[j].fault.location: continue
                if examined>=max_combinations: return result(reason='work_limit')
                examined+=1
                if ss[i].logical^ss[j].logical: return result(witness(c,[ss[i],ss[j]]))
    completed=2
    if max_weight==2: return result()
    # Meet in the middle: D_i xor D_j is matched to a stored singleton D_k.
    for i,a in enumerate(ss):
        for j in range(i+1,len(ss)):
            b=ss[j]
            if a.fault.location==b.fault.location: continue
            if examined>=max_combinations: return result(reason='work_limit')
            examined+=1
            for k in groups.get(a.detection^b.detection,()):
                if k<=j or ss[k].fault.location in (a.fault.location,b.fault.location): continue
                if examined>=max_combinations: return result(reason='work_limit')
                examined+=1
                if a.logical^b.logical^ss[k].logical: return result(witness(c,[a,b,ss[k]]))
    completed=3
    for weight in range(4,max_weight+1):
        for group in combinations(ss,weight):
            if examined>=max_combinations: return result(reason='work_limit')
            examined+=1
            if len({s.fault.location for s in group})!=weight: continue
            d=l=0
            for s in group: d^=s.detectors; l^=s.logical
            if not d and l: return result(witness(c,group))
        completed=weight
    return result()
