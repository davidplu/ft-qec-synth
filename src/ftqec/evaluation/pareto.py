MINIMIZE=('Q','D','QD','two_q_gates')

def dominates(a,b,include_distance=True):
    va=[a['resources'][m] for m in MINIMIZE]; vb=[b['resources'][m] for m in MINIMIZE]
    if include_distance:
        va.append(-a['bounds']['lower_bound']); vb.append(-b['bounds']['lower_bound'])
    return all(x<=y for x,y in zip(va,vb)) and any(x<y for x,y in zip(va,vb))

def frontier(records):
    # Keep one representative per identical objective vector. Full records preserve all alternatives.
    unique={}
    for a in records:
        key=tuple(a['resources'][m] for m in MINIMIZE)+(a['bounds']['lower_bound'],)
        old=unique.get(key)
        if old is None or a.get('architecture_id','')<old.get('architecture_id',''): unique[key]=a
    values=list(unique.values())
    return [a for a in values if not any(dominates(b,a) for b in values if b is not a)]
