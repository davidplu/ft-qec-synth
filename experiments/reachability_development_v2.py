"""Additional generic pilot templates, never supplied to final search."""
from dataclasses import replace
from development_v2 import ROOT,OUT,dump,assert_frozen
from ftqec.codes.stabilizer import StabilizerCode
from ftqec.architectures.generators import generate
from ftqec.circuits.memory import MemoryConfig
from ftqec.search.cegis import SearchConfig,evaluate_memory
from ftqec.faults.exclusion import verify_exclusion
import json

def main():
    assert_frozen();items=json.loads((OUT/'screening.json').read_text());results=[]
    for s in items:
        if s['classification']!='OPEN_HEADROOM' or s['difficulty']!='USEFUL':continue
        code=StabilizerCode.from_dict(json.loads((ROOT/s['code_path']).read_text()));base=next(generate(code,1));rows=[]
        for template in ('prefix','suffix','partitions','halves'):
            intervals=[]
            for o in base.orders:
                width=len(o);points=sorted({0,width,*[max(1,width*i//4) for i in range(1,4)]})
                if template=='prefix':fs=[(0,q) for q in points[1:]]
                elif template=='suffix':fs=[(q,width) for q in points[:-1]]
                elif template=='partitions':fs=list(zip(points,points[1:]))
                else:fs=[(0,width),(0,max(1,width//2)),(max(1,width//2),width)]
                intervals.append(tuple((a,b) for a,b in fs if a<b))
            for reverse in (False,True):
                child=replace(base,flag_intervals=tuple(intervals),orders=tuple(tuple(reversed(o)) if reverse else o for o in base.orders),
                    syndrome_budget=len(base.orders),ancilla_assignment=tuple(range(len(base.orders))),parallelism=1)
                rec,c=evaluate_memory(code,child,MemoryConfig(3,s['basis']),SearchConfig(target_dc=s['d_target'],decoder_weight=0))
                if rec['bounds']['lower_bound']>=s['d_target']:
                    rec['independent_exclusion']=verify_exclusion(c,s['d_target']-1);assert rec['independent_exclusion']['verified']
                rows.append({'template':template,'reverse':reverse,**rec})
        result={'task':s['task'],'target':s['d_target'],'reachable':any(r['bounds']['lower_bound']>=s['d_target'] for r in rows),
                'fixed_generic_constructions':rows,'algorithm_modified':False}
        results.append(result);dump(OUT/'additional_reachability.json',results)
        print(json.dumps({'additional_reachability':s['task'],'reachable':result['reachable']}),flush=True)

if __name__=='__main__':main()
