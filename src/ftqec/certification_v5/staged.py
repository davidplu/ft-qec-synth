"""Deterministic Pareto relevance and separately accounted certification work."""
from dataclasses import dataclass, field
from ..resource_synthesis.pareto import frontier, dominates
from ..resource_synthesis.certification import METRICS, classify, SignatureCache, independent_audit
from .exact import certify
from .low_audit import audit as independent_audit


@dataclass
class Budget:
    limit: int = 20000000
    used: int = 0
    candidate_evaluations: int = 0
    events: list = field(default_factory=list)
    @property
    def remaining(self): return max(0, self.limit-self.used)


def unknown_frontier(records):
    """Keep UNKNOWNs which could enter the true frontier; never promote by optimism."""
    valid = [r for r in records if r['region']=='VALID']
    return frontier([r for r in records if r['region']=='UNKNOWN' and
                     not any(dominates(v,r) for v in valid)])


def priority(record, records, target):
    potential = frontier([r for r in records if r['region'] in ('VALID','UNKNOWN')])
    extremes = sum(record['resources'][m] == min((r['resources'][m] for r in potential),default=-1)
                   for m in METRICS)
    return (-extremes, target-record['bounds']['lower_bound'],
            record['bounds'].get('signature_types',record['bounds'].get('fault_variants',0)),record['architecture_id'])


def escalate(record, circuit, target, budget, cache=None, reason='optimistic Pareto frontier',start_tier=1,count_candidate=True):
    if record['region']!='UNKNOWN': return record
    cache = cache or SignatureCache(); signatures,_ = cache.get(circuit)
    if count_candidate:budget.candidate_evaluations += 1
    rec = dict(record); previous = rec['bounds']; stages = []
    for tier, cap in enumerate((8192,65536,1048576),1):
        if tier<start_tier:continue
        allowance = min(cap,budget.remaining)
        if not allowance: break
        bounds = certify(circuit,signatures,target,allowance)
        budget.used += bounds['combinations_examined']
        # Independent evidence intervals intersect; a cap never erases earlier evidence.
        bounds['lower_bound'] = max(bounds['lower_bound'],previous['lower_bound'])
        uppers = [b.get('upper_bound') for b in (previous,bounds) if b.get('upper_bound') is not None]
        if uppers:
            upper = min(uppers)
            if previous.get('upper_bound') == upper and bounds.get('upper_bound') != upper:
                bounds['witness'] = previous.get('witness')
            bounds['upper_bound'] = upper
        if bounds.get('upper_bound') is not None and bounds['lower_bound']>bounds['upper_bound']:
            raise ArithmeticError('Contradictory independently checkable evidence')
        region = classify(bounds,target)
        event = dict(architecture_id=record['architecture_id'],reason=reason,tier=tier,
                     allowance=allowance,work=bounds['combinations_examined'],region=region,
                     runtime_seconds=bounds['runtime_seconds'],profile=bounds['profile'])
        stages.append(event); budget.events.append(event)
        rec.update(bounds=bounds,region=region,certification_stages=stages)
        previous = bounds
        if region!='UNKNOWN': break
    if rec['region']=='VALID' and target<=4:
        audit=independent_audit(rec,circuit,target)
        if not audit['verified']: raise ArithmeticError('Independent promotion exclusion failed')
        rec['independent_audit']=audit
    return rec
