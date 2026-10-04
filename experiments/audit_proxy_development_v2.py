"""Independent resolution of native proxy caps; diagnostic only."""
import gzip,json,time
from development_v2 import OUT,dump,assert_frozen
from ftqec.codes.stabilizer import StabilizerCode
from ftqec.architectures.candidate import Candidate
from ftqec.circuits.memory import MemoryConfig,build_memory
from ftqec.faults.exclusion import verify_exclusion

def main():
    assert_frozen();rows=json.loads((OUT/'proxies.json').read_text());details=[]
    for p in rows:
        with gzip.open(OUT/'proxy_raw'/f"n{p['n']}.json.gz",'rt') as f:run=json.load(f)
        code=StabilizerCode.from_dict(run['code']);start=time.perf_counter();seen=set();proved=None
        for rec in run['records']:
            if rec['architecture_id'] in seen:continue
            seen.add(rec['architecture_id']);b=rec['bounds']
            if b['upper_bound'] is not None and b['upper_bound']<3:continue
            c=build_memory(code,Candidate.from_dict(rec['candidate']),MemoryConfig(**run['memory_configuration']))
            cert=verify_exclusion(c,2)
            details.append({'n':p['n'],'architecture_id':rec['architecture_id'],'native_bounds':b,'independent_exclusion':cert})
            if cert['verified']:
                proved={'node':rec['evaluation_index'],'architecture_id':rec['architecture_id'],'native_lower_bound':b['lower_bound'],
                        'independent_lower_bound':3,'exclusion':cert};break
        elapsed=time.perf_counter()-start
        p['native_search_seconds']=p.get('native_search_seconds',p['seconds']);p['independent_audit_seconds']=elapsed
        p['seconds']=p['native_search_seconds']+elapsed;p['independently_resolved_target_architecture']=proved
        if proved:p['independent_best_exclusion']=proved['exclusion'];p['best_dc_independent_lower_bound']=3
        dump(OUT/'proxy_independent_audit.json',details);dump(OUT/'proxies.json',rows)
        print(json.dumps({'proxy':p['n'],'independent_target_proved':bool(proved),'audit_seconds':elapsed}),flush=True)

if __name__=='__main__':main()
