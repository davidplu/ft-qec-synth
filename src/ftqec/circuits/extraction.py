from .model import Circuit
from .gadgets import append_gadget

def build(code,candidate):
    candidate.validate(code)
    syn=tuple(range(code.n,code.n+candidate.syndrome_budget))
    # Each syndrome slot owns flag slots, reused between checks.
    counts=[max([len(candidate.flag_intervals[i]) for i,a in enumerate(candidate.ancilla_assignment) if a==slot]+[0])
            for slot in range(candidate.syndrome_budget)]
    flags=[]; pools=[]
    for count in counts:
        pool=tuple(range(code.n+len(syn)+len(flags),code.n+len(syn)+len(flags)+count))
        pools.append(pool); flags.extend(pool)
    c=Circuit(code,syn,tuple(flags)); tails={}; lanes={}
    for position,i in enumerate(candidate.check_order):
        slot=candidate.ancilla_assignment[i]; lane=position%candidate.parallelism
        deps=tuple(sorted(set(t for t in [tails.get(slot),lanes.get(lane)] if t is not None)))
        tail=append_gadget(c,i,candidate.orders[i],candidate.flag_intervals[i],syn[slot],pools[slot],deps)
        tails[slot]=tail; lanes[lane]=tail
    c.validate(); return c
