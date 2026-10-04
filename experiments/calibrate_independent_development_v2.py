"""Resolve capped initial-population tiers before benchmark admission."""
import gzip,json
from development_v2 import OUT,ROOT,dump,assert_frozen
from ftqec.codes.stabilizer import StabilizerCode
from ftqec.architectures.candidate import Candidate
from ftqec.circuits.memory import MemoryConfig,build_memory
from ftqec.faults.exclusion import verify_exclusion
from ftqec.faults.signatures import enumerate_faults
from ftqec.faults.verification import replay

def main():
    assert_frozen();screen=json.loads((OUT/'screening.json').read_text());audits=[]
    dump(OUT/'screening_before_independent_calibration.json',screen)
    for s in screen:
        if s['difficulty']!='USEFUL':continue
        code=StabilizerCode.from_dict(json.loads((ROOT/s['code_path']).read_text()));bounds=[]
        for seed in (0,1,2):
            with gzip.open(OUT/'screen'/f"{s['task']}-seed{seed}.json.gz",'rt',encoding='utf-8') as f:run=json.load(f)
            for rec in run['records']:
                b=rec['bounds'];lower=b['lower_bound'];certificate=None
                if lower<3 and b['upper_bound'] is None:
                    c=build_memory(code,Candidate.from_dict(rec['candidate']),MemoryConfig(3,s['basis']))
                    certificate=verify_exclusion(c,2)
                    if certificate['verified']:lower=3
                    else:
                        faults=list(enumerate_faults(c));group=[faults[i].to_dict() for i in certificate['counterexample_indices']]
                        effect=replay(c,group);assert effect['detector_outcomes']==0 and effect['logical_coset']
                        certificate['physical_counterexample']={'faults':group,'fault_count':len(group),**effect}
                audits.append({'task':s['task'],'seed':seed,'architecture_id':rec['architecture_id'],
                    'engine_lower_bound':b['lower_bound'],'independently_resolved_lower_bound':lower,'exclusion':certificate})
                bounds.append(lower)
        s['engine_d_initial']=s['d_initial'];s['independent_initial_bounds']=bounds
        if max(bounds)>s['d_initial']:
            s['d_initial']=max(bounds);s['d_target']=s['d_initial']+1
            s['initial_target_frequency_at_original_target']=sum(max(bounds[i:i+6])>=3 for i in range(0,18,6))/3
            if s['boundary']['distance']<=s['d_initial']:
                s['classification']='BOUNDARY_LIMITED';s['difficulty']='TOO_EASY'
            else:s['difficulty']='CERTIFICATION_TIER_LIMITED'
            s['independent_calibration_reason']='Native engine cap hid initial target-quality circuits; do not mistake certification censoring for architecture-search headroom.'
        print(json.dumps({'independent_calibration':s['task'],'initial':s['d_initial'],'difficulty':s['difficulty']}),flush=True)
        dump(OUT/'independent_initial_calibration.json',audits)
    dump(OUT/'screening.json',screen)

if __name__=='__main__':main()
