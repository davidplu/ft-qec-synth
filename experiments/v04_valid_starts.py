"""Supplemental generic prefix-protected starts, selected only by validity."""
from dataclasses import replace
from pathlib import Path
import json, random, sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
from v04_development import tasks,ROOT,OUT,SEEDS,assert_frozen,dump,write_run
from ftqec.codes.stabilizer import StabilizerCode
from ftqec.architectures.generators import generate
from ftqec.circuits.memory import MemoryConfig
from ftqec.resource_synthesis.design import Design
from ftqec.resource_synthesis.certification import evaluate
from ftqec.resource_synthesis.search import ResourceConfig,run_resource_search

def main():
    assert_frozen(); calibration=[]
    for task in [t for t in tasks() if t['task'] in ('steane7-X','affine15_k1-X','simplex15_k7-X')]:
        code=StabilizerCode.from_dict(json.loads((ROOT/task['code_path']).read_text())); memory=MemoryConfig(basis='X')
        for seed in SEEDS:
            a=next(iter(generate(code,1,seed))); rng=random.Random(seed)
            orders=[list(o) for o in a.orders]
            for o in orders: rng.shuffle(o)
            a=replace(a,orders=tuple(map(tuple,orders)),syndrome_budget=len(a.orders),
                ancilla_assignment=tuple(range(len(a.orders))),parallelism=1,
                flag_intervals=tuple(tuple((0,p) for p in range(1,len(o)+1)) for o in orders),terminal_repetitions=1)
            design=Design(a); rec,_=evaluate(code,design,memory)
            calibration.append({'task':task['task'],'seed':seed,'initial':rec})
            print('prefix_start',task['task'],seed,rec['region'],rec['bounds']['lower_bound'],flush=True)
            if rec['region']!='VALID': continue
            for variant in ('repair_only','repair_compress'):
                cfg=ResourceConfig(seed=seed,initial_population=1,strategy=variant)
                write_run(f'prefixprotected--{task["task"]}--{variant}--{seed}',
                          lambda cfg=cfg,d=design:run_resource_search(code,memory,cfg,[d]))
    dump(OUT/'prefix_starts.json',calibration)

if __name__=='__main__': main()
