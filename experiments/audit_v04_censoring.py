"""Bounded post-experiment censoring audit, separate from frozen endpoints."""
from pathlib import Path
import gzip,json
from v04_development import ROOT,OUT,assert_frozen,dump
from ftqec.codes.stabilizer import StabilizerCode
from ftqec.circuits.memory import MemoryConfig,build_memory
from ftqec.architectures.candidate import Candidate
from ftqec.resource_synthesis.design import Design
from ftqec.resource_synthesis.circuits import build_design
from ftqec.resource_synthesis.certification import METRICS
from ftqec.faults.exclusion import verify_exclusion
from ftqec.faults.signatures import enumerate_faults
from ftqec.faults.verification import replay

def main():
    assert_frozen(); rows=[]; seen={}
    sources=[]
    for path in sorted((OUT/'raw').glob('primary*.gz')):
        with gzip.open(path,'rt') as f: result=json.load(f)
        unknown=[r for r in result['records'] if r['bounds']['lower_bound']<3 and r['bounds'].get('upper_bound') is None
                 and r.get('region')!='INVALID_STRUCTURE']
        selected={}
        for m in METRICS:
            if unknown:
                r=min(unknown,key=lambda r:(r['resources'][m],r['architecture_id'])); selected[r['architecture_id']]=r
        for r in selected.values(): sources.append((path.name,result,r))
    for start in json.loads((OUT/'prefix_starts.json').read_text()):
        r=start['initial']
        if r['region']=='UNKNOWN':
            task=next(t for t in json.loads((OUT/'experiment_freeze.json').read_text())['tasks'] if t['task']==start['task'])
            sources.append((f'prefix_initial:{start["task"]}:{start["seed"]}',{
                'code':json.loads((ROOT/task['code_path']).read_text()),'memory_configuration':{'rounds':3,'basis':task['basis'],'logical_index':0,'noisy_input':False}},r))
    for name,result,r in sources:
        code=StabilizerCode.from_dict(result['code']); memory=MemoryConfig(**result['memory_configuration'])
        key=(code.input_hash,json.dumps(result['memory_configuration'],sort_keys=True),r['architecture_id'])
        if key not in seen:
            c=build_design(code,Design.from_dict(r['design']),memory) if 'design' in r else build_memory(code,Candidate.from_dict(r['candidate']),memory)
            audit=verify_exclusion(c,2)
            if not audit['verified']:
                faults=list(enumerate_faults(c)); group=[faults[i].to_dict() for i in audit['counterexample_indices']]
                physical=replay(c.to_dict(),group)
                if physical['detector_outcomes'] or not physical['logical_coset']: raise ArithmeticError('Censoring witness invalid')
                audit={**audit,'physical_faults':group,'physical_replay':physical}
            seen[key]=audit
        rows.append({'run':name,'architecture_id':r['architecture_id'],'native_bounds':r['bounds'],'resources':r['resources'],
            'independent_target_exclusion':seen[key],
            'interpretation':'native search remained UNKNOWN; this diagnostic does not rewrite frozen validity endpoints'})
    dump(OUT/'censoring_audit.json',{'selection':'up to four independent resource minima among UNKNOWN primary records; all UNKNOWN supplemental prefix starts',
        'records':rows,'unique_circuits':len(seen),'certified_target_afterwards':sum(r['independent_target_exclusion']['verified'] for r in rows)})
    print('censoring',len(rows),len(seen),sum(r['independent_target_exclusion']['verified'] for r in rows),flush=True)

if __name__=='__main__': main()
