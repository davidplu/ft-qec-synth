from dataclasses import replace

def mutate(candidate,rng,max_flags=2):
    m=len(candidate.orders)
    action=rng.randrange(7)
    if not m: return candidate
    i=rng.randrange(m)
    if action==0:
        orders=[list(o) for o in candidate.orders]
        if len(orders[i])>1:
            a,b=rng.sample(range(len(orders[i])),2); orders[i][a],orders[i][b]=orders[i][b],orders[i][a]
        return replace(candidate,orders=tuple(map(tuple,orders)))
    if action in (1,2,3):
        intervals=[list(f) for f in candidate.flag_intervals]; w=len(candidate.orders[i])
        if action==3 and intervals[i]: intervals[i].pop(rng.randrange(len(intervals[i])))
        elif w>1:
            interval=tuple(sorted(rng.sample(range(w+1),2)))
            if action==1 and intervals[i]: intervals[i][rng.randrange(len(intervals[i]))]=interval
            elif len(intervals[i])<max_flags: intervals[i].append(interval)
        return replace(candidate,flag_intervals=tuple(tuple(f) for f in intervals))
    if action==4:
        order=list(candidate.check_order); rng.shuffle(order); return replace(candidate,check_order=tuple(order))
    if action==5:
        budget=rng.randint(1,max(1,m))
        return replace(candidate,syndrome_budget=budget,ancilla_assignment=tuple(rng.randrange(budget) for _ in range(m)),parallelism=min(candidate.parallelism,budget))
    return replace(candidate,parallelism=rng.randint(1,candidate.syndrome_budget))
