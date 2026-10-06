"""V0.5 endpoint processing without changing the V0.4 candidate search."""
from dataclasses import asdict
from ..resource_synthesis.certification import SignatureCache
from ..resource_synthesis.circuits import build_design
from ..resource_synthesis.design import Design
from ..resource_synthesis.pareto import frontier,minima,tiers
from .staged import Budget,unknown_frontier,priority,escalate
from .descent import descend


def finish(code,memory,result,target=3,certification_work=20000000,descent_evaluations=256):
    rows=list({r['architecture_id']:r for r in result['records']}.values())
    budget=Budget(certification_work);cache=SignatureCache()
    native=frontier([r for r in rows if r['region']=='VALID'])
    for rec in sorted(unknown_frontier(rows),key=lambda r:priority(r,rows,target)):
        if rec['architecture_id'] not in {r['architecture_id'] for r in unknown_frontier(rows)}:continue
        circuit=build_design(code,Design.from_dict(rec['design']),memory)
        promoted=escalate(rec,circuit,target,budget,cache)
        rows=[promoted if r['architecture_id']==rec['architecture_id'] else r for r in rows]
    promoted=frontier([r for r in rows if r['region']=='VALID'])
    closure=descend(code,memory,promoted,target,budget,evaluation_limit=descent_evaluations)
    combined=list({r['architecture_id']:r for r in rows+closure['records']}.values())
    return {**result,'schema_version':'0.5','software_version':'0.5.0',
            'v04_search_records':result['records'],'records':combined,
            'native_frontier':[r['architecture_id'] for r in native],
            'promoted_frontier':[r['architecture_id'] for r in promoted],
            'frontier':closure['frontier'],'compression_descent':closure,
            'archives':{**result.get('archives',{}),'VALID_PARETO':closure['frontier'],
                        'UNKNOWN_PARETO':[r['architecture_id'] for r in unknown_frontier(combined)]},
            'certification_budget':asdict(budget),'distance_conditioned_frontiers':tiers(combined),
            'summary':dict(target_reached=bool(closure['frontier']),minima_at_target=closure['minima'],
                           native_minima=minima(native),promoted_minima=minima(promoted))}
