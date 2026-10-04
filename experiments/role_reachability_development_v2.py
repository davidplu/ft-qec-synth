"""Fixed readout-role constructive pilot, not a frozen search modification."""
from dataclasses import replace
from development_v2 import ROOT,OUT,dump,assert_frozen
from ftqec.codes.stabilizer import StabilizerCode
from ftqec.architectures.generators import generate
from ftqec.circuits.memory import MemoryConfig,build_memory
from ftqec.search.cegis import SearchConfig,evaluate_memory
from ftqec.faults.exclusion import verify_exclusion
import json

def main():
    assert_frozen();items=json.loads((OUT/'screening.json').read_text());results=[]
    for s in items:
        if s['classification']!='OPEN_HEADROOM' or s['difficulty']!='USEFUL':continue
        code=StabilizerCode.from_dict(json.loads((ROOT/s['code_path']).read_text()));base=next(generate(code,1));rows=[]
        axes=build_memory(code,base,MemoryConfig(3,s['basis'])).experiment['readout_axes']
        if len(set(axes))!=1:
            results.append({'task':s['task'],'reachable':False,'status':'UNIFORM_AXES_REQUIRED'});continue
        intervals=[]
        for p,o in zip(code.generators,base.orders):
            opposite=p.z.bit_count() if axes[0]=='X' else p.x.bit_count()
            width=len(o)
            if opposite==0:fs=[]
            elif opposite<=4:fs=[(0,width)]
            else:fs=[(0,q) for q in sorted({width,*[max(1,width*i//4) for i in range(1,4)]})]
            intervals.append(tuple(fs))
        for reverse in (False,True):
            child=replace(base,flag_intervals=tuple(intervals),orders=tuple(tuple(reversed(o)) if reverse else o for o in base.orders),
                syndrome_budget=len(base.orders),ancilla_assignment=tuple(range(len(base.orders))),parallelism=1)
            rec,c=evaluate_memory(code,child,MemoryConfig(3,s['basis']),SearchConfig(target_dc=s['d_target'],decoder_weight=0))
            if rec['bounds']['lower_bound']>=s['d_target']:
                rec['independent_exclusion']=verify_exclusion(c,s['d_target']-1);assert rec['independent_exclusion']['verified']
            rows.append({'template':'uniform_readout_role_prefixes','reverse':reverse,**rec})
        result={'task':s['task'],'target':s['d_target'],'reachable':any(r['bounds']['lower_bound']>=s['d_target'] for r in rows),
                'fixed_generic_constructions':rows,'algorithm_modified':False}
        results.append(result);dump(OUT/'role_reachability.json',results)
        print(json.dumps({'role_reachability':s['task'],'reachable':result['reachable']}),flush=True)

if __name__=='__main__':main()
