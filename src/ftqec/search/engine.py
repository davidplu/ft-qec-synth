import random, time, subprocess
from pathlib import Path
from ..architectures.generators import generate
from ..circuits.extraction import build
from ..evaluation.resources import resources
from ..evaluation.pareto import frontier, dominates
from ..evaluation.scoring import beam_order
from ..faults.signatures import signatures
from ..faults.search import search_faults
from .mutations import mutate

MODEL='independent Pauli faults at distinct circuit locations; ideal initial and final syndrome boundaries'

def evaluate(code,candidate,max_weight=2,max_combinations=2000000,idles=False,stage_a_frontier=(),required_distance=2):
    if max_weight not in (1,2,3) or not 1<=required_distance<=max_weight+1: raise ValueError('Invalid weight/acceptance threshold')
    start=time.perf_counter(); c=build(code,candidate); r=resources(c)
    rec=dict(architecture_id=candidate.id,candidate=candidate.to_dict(),resources=r,
             bounds=dict(status='UNRESOLVED',lower_bound=1,upper_bound=None),stage='A',rejection=None)
    # Resource pruning is safe only against a candidate certified through the requested weight.
    if any(b['bounds'].get('excluded_through',0)>=max_weight and dominates(b,rec,False) for b in stage_a_frontier):
        rec['rejection']='A_resource_dominated'; rec['runtime_seconds']=time.perf_counter()-start; return rec
    st=time.perf_counter(); ss=signatures(c,idles); rec['signature_seconds']=time.perf_counter()-st
    st=time.perf_counter()
    for weight,stage in [(1,'B'),(2,'C'),(3,'D')][:max_weight]:
        rec['stage']=stage; bounds=search_faults(c,ss,weight,max_combinations); rec['bounds']=bounds
        if bounds['witness']:
            rec['screening_stop']=stage+'_logical_witness'
            if weight<required_distance: rec['rejection']=stage+'_logical_witness'
            break
        if bounds['excluded_through']<weight:
            rec['screening_stop']=stage+'_work_limit'
            if bounds['excluded_through']<required_distance-1: rec['rejection']=stage+'_work_limit'
            break
    rec['fault_search_seconds']=time.perf_counter()-st
    rec['runtime_seconds']=time.perf_counter()-start
    return rec

def software_commit():
    try:
        p=subprocess.run(['git','-c',f'safe.directory={Path.cwd().as_posix()}','rev-parse','HEAD'],capture_output=True,text=True,timeout=3)
        return p.stdout.strip() if p.returncode==0 else None
    except (OSError,subprocess.TimeoutExpired): return None

def search(code,budget=100,seed=0,max_weight=2,max_combinations=2000000,beam_width=12,idles=False,required_distance=2):
    if budget<1 or beam_width<1: raise ValueError('Positive budget and beam width required')
    if max_weight not in (1,2,3): raise ValueError('Weight must be 1,2,3')
    if not 1<=required_distance<=max_weight+1: raise ValueError('Required distance must be between 1 and max_weight+1')
    start=time.perf_counter(); rng=random.Random(seed); records=[]; seen=set(); beam=[]
    queue=list(generate(code,min(budget,32),seed)); attempts=0; accepted_front=[]; explored_front=[]
    while len(records)<budget and attempts<budget*50:
        attempts+=1
        if queue: candidate=queue.pop(0)
        elif beam: candidate=mutate(rng.choice(beam),rng)
        else: break
        if candidate.id in seen: continue
        seen.add(candidate.id)
        rec=evaluate(code,candidate,max_weight,max_combinations,idles,accepted_front,required_distance); records.append(rec)
        explored_front=frontier(explored_front+[rec])
        if not rec['rejection']: accepted_front=frontier(accepted_front+[rec])
        # Failed candidates remain exploratory parents if the certified beam is empty.
        pool=accepted_front or explored_front
        beam=[type(candidate).from_dict(r['candidate']) for r in sorted(pool,key=beam_order)[:beam_width]]
    counts={reason:sum(r['rejection']==reason for r in records) for reason in sorted(set(r['rejection'] for r in records if r['rejection']))}
    return dict(schema_version='0.1',code=code.to_dict(),code_input_hash=code.input_hash,
                software_version='0.2.0',software_git_commit=software_commit(),seed=seed,
                configuration=dict(budget=budget,max_weight=max_weight,max_combinations=max_combinations,beam_width=beam_width,idles=idles,required_distance=required_distance),
                fault_model=MODEL,candidates_evaluated=len(records),rejections=counts,
                stage_outcomes={stage:sum(r.get('screening_stop')==stage for r in records) for stage in sorted(set(r.get('screening_stop') for r in records if r.get('screening_stop')))},
                frontier=accepted_front,exploratory_frontier=explored_front,records=records,
                runtime_seconds=time.perf_counter()-start)
