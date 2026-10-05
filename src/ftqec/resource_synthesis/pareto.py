"""Distance-conditioned resource archives without a universal scalar score."""
from .certification import METRICS, classify


def dominates(a,b):
    return all(a['resources'][m] <= b['resources'][m] for m in METRICS) and any(a['resources'][m] < b['resources'][m] for m in METRICS)


def frontier(records):
    unique = {r['architecture_id']:r for r in records}
    rows = list(unique.values())
    return [r for r in rows if not any(dominates(s,r) for s in rows if s is not r)]


def minima(records):
    return {m:min((r['resources'][m] for r in records),default=None) for m in METRICS}


def tiers(records):
    maximum = max((r['bounds']['lower_bound'] for r in records if r.get('ideal_validation',{}).get('verified',True)),default=1)
    result={}
    for t in range(1,maximum+1):
        f=frontier([r for r in records if r['bounds']['lower_bound']>=t and r.get('ideal_validation',{}).get('verified',True)])
        result[str(t)]={'architecture_ids':[r['architecture_id'] for r in f],'minima':minima(f)}
    return result


class Archives:
    def __init__(self,target,cap=12):
        self.target=target; self.cap=cap; self.valid=[]; self.near=[]

    def update(self,record):
        region = record['region']
        if region == 'VALID': self.valid = self._bound(frontier(self.valid+[record]))
        elif region == 'INVALID' and record['bounds']['upper_bound'] == self.target-1:
            self.near = self._bound(frontier(self.near+[record]))

    def _bound(self,records):
        # Preserve each independent metric extreme, then round-robin tradeoffs.
        selected=[]
        for m in METRICS:
            for r in sorted(records,key=lambda r:(r['resources'][m],r['architecture_id'])):
                if r not in selected: selected.append(r); break
        for r in sorted(records,key=lambda r:r['architecture_id']):
            if r not in selected: selected.append(r)
        return selected[:self.cap]

    def to_dict(self):
        return {'VALID_PARETO':[r['architecture_id'] for r in self.valid],
                'NEAR_VALID_PARETO':[r['architecture_id'] for r in self.near],
                'archive_cap':self.cap,'truncated':len(self.valid)>=self.cap or len(self.near)>=self.cap}
