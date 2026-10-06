"""Optional bounded two-edit rescue after single-edit closure or a documented block."""
from ..resource_synthesis.design import Design
from ..resource_synthesis.circuits import build_design
from ..resource_synthesis.operators import compressions
from ..resource_synthesis.certification import SignatureCache,METRICS
from ..resource_synthesis.pareto import frontier
from ..evaluation.resources import resources
from .descent import constraint


def depth_two(code,memory,parent,single_audit,target,budget,pair_limit=32):
    if single_audit['label'] not in ('LOCALLY_PROTECTION_MINIMAL_1','UNRESOLVED_MINIMALITY'):
        raise ValueError('Exhaust or explicitly bound single-edit descent before depth-two rescue')
    if pair_limit<0:raise ValueError('Negative pair limit')
    d=Design.from_dict(parent['design']);c=build_design(code,d,memory);cache=SignatureCache()
    first=list(compressions(d,c,memory.rounds));by_metric=[]
    for m in METRICS:
        ordered=sorted(first,key=lambda x:(resources(build_design(code,x[0],memory))[m],x[0].id))
        for item in ordered[:8]:
            if item not in by_metric:by_metric.append(item)
    results=[];ancestry=[];seen=set();complete=len(by_metric)==len(first)
    for middle,op1,feature1 in by_metric:
        mc=build_design(code,middle,memory)
        for child,op2,feature2 in compressions(middle,mc,memory.rounds):
            if child.id in seen:continue
            seen.add(child.id);cc=build_design(code,child,memory)
            if not any(resources(cc)[m]<parent['resources'][m] for m in METRICS):continue
            if len(results)>=pair_limit or not budget.remaining:
                complete=False;break
            r,_=constraint(code,child,memory,target,budget,cache);results.append(r)
            ancestry.append(dict(parent_id=parent['architecture_id'],intermediate_id=middle.id,
                child_id=child.id,operators=[op1,op2],features=[feature1,feature2]))
        if len(results)>=pair_limit or not budget.remaining:break
    valid=frontier([r for r in results if r['region']=='VALID'])
    return dict(records=results,ancestry=ancestry,frontier=[r['architecture_id'] for r in valid],
                pair_limit=pair_limit,complete=complete,global_optimality_claim=False,
                label='NOT_LOCALLY_PROTECTION_MINIMAL' if valid else
                'LOCALLY_PROTECTION_MINIMAL_2' if complete and all(r['region']!='UNKNOWN' for r in results)
                else 'UNRESOLVED_MINIMALITY')
