"""Bounded Pareto compression closure; unresolved budgets never imply minimality."""
import time
from ..resource_synthesis.design import Design
from ..resource_synthesis.circuits import build_design, validate_ideal
from ..resource_synthesis.certification import SignatureCache, fingerprint, classify, METRICS, independent_audit
from ..resource_synthesis.operators import compressions
from ..resource_synthesis.pareto import frontier, dominates
from ..evaluation.resources import resources
from .exact import certify
from .staged import escalate
from .low_audit import audit as independent_audit


def constraint(code,design,memory,target,budget,cache,parent_hash=None):
    started=time.perf_counter();c=build_design(code,design,memory);built=time.perf_counter()
    ideal=validate_ideal(c);checked=time.perf_counter()
    r=dict(architecture_id=design.id,design=design.to_dict(),resources=resources(c),
           circuit_hash=fingerprint(c),ideal_validation=ideal)
    if not ideal['verified']:
        r.update(region='INVALID_STRUCTURE',bounds=dict(lower_bound=1,upper_bound=None,witness=None,
                                                       status='INVALID_IDEAL_CIRCUIT'))
        r['phase_seconds']=dict(build=built-started,ideal=checked-built)
        return r,c
    ss,_=cache.get(c,parent_hash); budget.candidate_evaluations+=1
    signed=time.perf_counter()
    b=certify(c,ss,target,min(8192,budget.remaining)); budget.used+=b['combinations_examined']
    r.update(bounds=b,region=classify(b,target))
    budget.events.append(dict(architecture_id=design.id,reason='resource-reducing compression edit',tier=1,
        work=b['combinations_examined'],region=r['region'],runtime_seconds=b['runtime_seconds'],profile=b['profile']))
    if r['region']=='UNKNOWN': r=escalate(r,c,target,budget,cache,'resource-reducing compression edit',start_tier=2,count_candidate=False)
    certified=time.perf_counter()
    if r['region']=='VALID':r['independent_audit']=dict(verified=None,status='PENDING_FINAL_FRONTIER_AUDIT')
    r['phase_seconds']=dict(build=built-started,ideal=checked-built,signatures=signed-checked,
        certification=certified-signed,independent_verification=time.perf_counter()-certified)
    # Each circuit is evaluated once. Retaining every suffix transfer matrix
    # across a long closure consumes quadratic storage without useful reuse.
    cache.entries.clear()
    return r,c


def resource_points(rows):
    """One implementation per numeric Pareto point; retain alternatives in records."""
    selected={}
    for row in sorted(frontier(rows),key=lambda r:r['architecture_id']):
        key=tuple(row['resources'][m] for m in METRICS)
        selected.setdefault(key,row)
    return list(selected.values())


def descend(code,memory,parents,target,budget,evaluation_limit=256,shared=None):
    started=time.perf_counter(); cache=SignatureCache(); evaluated=shared if shared is not None else {}
    records={r['architecture_id']:r for r in parents}; pending=list(parents); finished=set(); proposals=[]; audits={}; states={}
    count=0; stopped=False
    while pending:
        current=resource_points([r for r in records.values() if r['region']=='VALID'])
        ids={r['architecture_id'] for r in current}
        pending=[r for r in pending if r['architecture_id'] in ids and r['architecture_id'] not in finished]
        pending.extend(r for r in current if r['architecture_id'] not in finished and r not in pending)
        if not pending:break
        if count>=evaluation_limit or not budget.remaining:stopped=True;break
        chosen=[]
        for metric in METRICS:
            r=min(pending,key=lambda x:(x['resources'][metric],tuple(x['resources'][m] for m in METRICS if m!=metric),x['architecture_id']))
            if r not in chosen:chosen.append(r)
        parent=chosen[0];pid=parent['architecture_id']
        if pid not in states:
            d=Design.from_dict(parent['design']);c=build_design(code,d,memory);unique={}
            for child,op,feature in compressions(d,c,memory.rounds):unique.setdefault(child.id,(child,op,feature))
            options=[]
            # Ordering uses component cost estimates; actual resources are always
            # obtained from a fresh schedule before evaluating or accepting edits.
            # Building every speculative neighbor here was the profiling bottleneck.
            epochs={}; keys={}
            from ..resource_synthesis.circuits import op_key
            for physical in c.operations:
                if physical.gate=='BARRIER':continue
                for mapping,key in ((epochs,(physical.round_index,physical.check)),(keys,op_key(physical))):
                    values=mapping.setdefault(key,[0,0]);values[0]+=1
                    values[1]+=physical.gate in ('CX','CZ','SWAP')
            for child,op,feature in unique.values():
                if op=='remove_redundant_terminal_verification':continue  # classical zero resource cost
                removed=two=0;qsaving=0
                new_epochs=set(child.omitted_checks)-set(d.omitted_checks)
                for key in new_epochs:
                    a,b=epochs.get(key,(0,0));removed+=a;two+=b
                for key in set(child.omitted_operations)-set(d.omitted_operations):
                    a,b=keys.get(key,(0,0));removed+=a;two+=b
                if op in ('remove_flag_ancilla','reuse_syndrome_ancilla','reuse_flag_ancilla'):qsaving=1
                if op=='remove_cat_verification':
                    qsaving=1;removed=sum('verify' in (x.role or '') for x in c.operations)
                    two=sum('verify' in (x.role or '') and x.gate in ('CX','CZ') for x in c.operations)
                if op in ('merge_flag_intervals','remove_flag_ancilla'):removed=max(removed,2*memory.rounds);two=max(two,2*memory.rounds)
                if op=='remove_redundant_terminal_round':
                    removed=sum(x.round_index==memory.rounds for x in c.operations)
                    two=sum(x.round_index==memory.rounds and x.gate in ('CX','CZ') for x in c.operations)
                if op=='increase_safe_parallelism':removed=max(removed,parent['resources']['D']//2)
                rr=dict(parent['resources']);rr['Q']=max(code.n,rr['Q']-qsaving)
                rr['D']=max(1,rr['D']-removed);rr['QD']=rr['Q']*rr['D'];rr['two_q_gates']=max(0,rr['two_q_gates']-two)
                options.append((child,op,feature,rr))
            # Interleave independent metric rankings. Process only eight proposals
            # before allowing a better descendant to become the next incumbent.
            rankings={m:sorted(options,key=lambda x:(x[3][m],tuple(x[3][mm] for mm in METRICS if mm!=m),x[0].id)) for m in METRICS}
            queue=[];seen=set()
            for offset in range(len(options)):
                for m in METRICS:
                    item=rankings[m][offset]
                    if item[0].id not in seen:queue.append(item);seen.add(item[0].id)
            states[pid]=dict(queue=queue,cursor=0,rows=[],valid_children=0)
        state=states[pid]
        for _ in range(8):
            if state['cursor']>=len(state['queue']):break
            if count>=evaluation_limit or not budget.remaining:stopped=True;break
            child,op,feature,_=state['queue'][state['cursor']];state['cursor']+=1
            key=(code.input_hash,str(memory),target,child.id)
            if key not in evaluated:
                actual=resources(build_design(code,child,memory))
                if not any(actual[m]<parent['resources'][m] for m in METRICS):continue
            if key in evaluated:rec=evaluated[key]
            else:
                rec,_=constraint(code,child,memory,target,budget,cache,parent['circuit_hash'])
                evaluated[key]=rec;count+=1
            if not any(rec['resources'][m]<parent['resources'][m] for m in METRICS):continue
            state['rows'].append(dict(child_id=child.id,operator=op,feature=feature,region=rec['region'],bounds=rec['bounds']))
            proposals.append(dict(parent_id=pid,child_id=child.id,operator=op,feature=feature))
            records[child.id]=rec;state['valid_children']+=rec['region']=='VALID'
        complete=state['cursor']==len(state['queue'])
        if complete:finished.add(pid)
        label=('NOT_LOCALLY_PROTECTION_MINIMAL' if state['valid_children'] else
               'UNRESOLVED_MINIMALITY' if not complete or any(x['region']=='UNKNOWN' for x in state['rows'])
               else 'LOCALLY_PROTECTION_MINIMAL_1')
        audits[pid]=dict(label=label,complete=complete,edits=state['rows'],
            remaining_edit_ids=[x[0].id for x in state['queue'][state['cursor']:]],global_optimality_claim=False)
        if stopped:break
    final=resource_points([r for r in records.values() if r['region']=='VALID'])
    for r in final:
        if not r.get('independent_audit',{}).get('verified') and target<=4:
            cc=build_design(code,Design.from_dict(r['design']),memory)
            verified=independent_audit(r,cc,target)
            if not verified['verified']:raise ArithmeticError('Independent final descent exclusion failed')
            r['independent_audit']=verified
    for r in final:
        audits.setdefault(r['architecture_id'],dict(label='UNRESOLVED_MINIMALITY',complete=False,
            reason='descent_budget',edits=[],global_optimality_claim=False))
    return dict(records=list(records.values()),frontier=[r['architecture_id'] for r in final],
        audits=audits,proposals=proposals,new_evaluations=count,evaluation_limit=evaluation_limit,
        queue_batch=8,stopped_by_budget=stopped,runtime_seconds=time.perf_counter()-started,
        equivalent_resource_alternatives_retained=True,
        minima={m:min((r['resources'][m] for r in final),default=None) for m in METRICS})
