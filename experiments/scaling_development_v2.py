"""Fixed-architecture fault-weight/round scaling on unrelated proxies."""
from dataclasses import replace
from development_v2 import OUT,BENCH,ROOT,dump,assert_frozen
from compare_development_v2 import rss
from ftqec.codes.stabilizer import StabilizerCode
from ftqec.architectures.generators import generate
from ftqec.circuits.memory import MemoryConfig
from ftqec.search.cegis import SearchConfig,evaluate_memory
import json

def main():
    assert_frozen();rows=[]
    for path in sorted((BENCH/'proxies').glob('*.json')):
        code=StabilizerCode.from_dict(json.loads(path.read_text()));base=next(generate(code,1))
        # A deterministic generic fully flagged circuit, not an optimized input.
        child=replace(base,flag_intervals=tuple(tuple((0,len(o)) for _ in range(3)) for o in base.orders),
                      syndrome_budget=len(base.orders),ancilla_assignment=tuple(range(len(base.orders))),parallelism=1)
        for rounds in (1,3):
            for w in (1,2,3):
                rec,c=evaluate_memory(code,child,MemoryConfig(rounds,'Z'),SearchConfig(max_weight=w,target_dc=min(3,w+1),decoder_weight=0))
                b=rec['bounds'];seconds=rec['fault_search_seconds']
                rows.append({'proxy':code.name,'n':code.n,'checks':len(code.generators),'rounds':rounds,'requested_fault_weight':w,
                    'bounds':b,'resources':rec['resources'],'total_seconds':rec['runtime_seconds'],
                    'signature_seconds':rec['signature_seconds'],'certification_seconds':seconds,
                    'fault_combinations_per_sec':b['combinations_examined']/seconds if seconds else None,
                    'memory':rss(),'architecture_id':child.id,'work_cap':200000})
                dump(OUT/'fault_weight_scaling.json',rows)
                print(json.dumps({k:rows[-1][k] for k in ('n','rounds','requested_fault_weight','total_seconds')}),flush=True)

if __name__=='__main__':main()
