"""Prospective, resumable V0.4 experiments; no held-out architecture imports."""
from dataclasses import replace, asdict
from pathlib import Path
from hashlib import sha256
import argparse, gzip, json, time, subprocess
from ftqec.codes.stabilizer import StabilizerCode
from ftqec.architectures.generators import generate
from ftqec.circuits.memory import MemoryConfig, build_memory
from ftqec.search.malignant import MalignantConfig, run_malignant_search
from ftqec.faults.verification import verify_witness
from ftqec.faults.exclusion import verify_exclusion
from ftqec.resource_synthesis.design import Design
from ftqec.resource_synthesis.certification import evaluate, METRICS
from ftqec.resource_synthesis.search import ResourceConfig, run_resource_search, protection_audit
from ftqec.resource_synthesis.circuits import build_design
from ftqec.resource_synthesis.pareto import frontier, minima, tiers

ROOT=Path(__file__).resolve().parents[1]; OUT=ROOT/'results/v0.4'
SEEDS=(10,11,12); BUDGET=48


def dump(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,indent=2,allow_nan=False)+'\n',encoding='utf-8')


def historical_check():
    p=json.loads((OUT/'preservation.json').read_text())
    for name,h in p['hashes'].items():
        if sha256((ROOT/name).read_bytes()).hexdigest()!=h: raise AssertionError('Historical baseline changed: '+name)
    return len(p['hashes'])


def tasks():
    return json.loads((ROOT/'benchmarks/development_v2/MANIFEST.json').read_text())['tasks']


def freeze():
    historical_check()
    files=[p for base in ('src/ftqec/resource_synthesis','tests/test_resource_synthesis.py','experiments/v04_development.py','docs/V0_4_PROTOCOL.md','benchmarks/development_v2')
           for p in ([ROOT/base] if (ROOT/base).is_file() else (ROOT/base).rglob('*')) if p.is_file() and '__pycache__' not in p.parts]
    git=['git','-c',f'safe.directory={ROOT.as_posix()}']
    commit=subprocess.check_output(git+['rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    dump(OUT/'experiment_freeze.json',{'algorithm_commit':commit,'baseline_commit':json.loads((OUT/'preservation.json').read_text())['baseline_commit'],
        'protocol':'docs/V0_4_PROTOCOL.md','seeds':SEEDS,'budget':BUDGET,
        'primary_variants':['v03','v04','resource','random','no_basis','no_family'],
        'configuration':asdict(ResourceConfig()),'tasks':tasks(),
        'hashes':{p.relative_to(ROOT).as_posix():sha256(p.read_bytes()).hexdigest() for p in files}})


def assert_frozen():
    f=json.loads((OUT/'experiment_freeze.json').read_text())
    for name,h in f['hashes'].items():
        if sha256((ROOT/name).read_bytes()).hexdigest()!=h: raise AssertionError('V0.4 algorithm/input changed: '+name)
    historical_check(); return f


def baseline_result(code,memory,variant,seed):
    result=run_malignant_search(code,memory,MalignantConfig(budget=BUDGET,seed=seed,strategy=variant))
    valid=[r for r in result['records'] if r['bounds']['lower_bound']>=3]
    f=frontier(valid); result['resource_summary']={'target_reached':bool(f),'minima_at_target':minima(f)}
    result['resource_frontier']=[r['architecture_id'] for r in f]
    result['independent_final_audits']=[]
    for r in f:
        from ftqec.architectures.candidate import Candidate
        c=build_memory(code,Candidate.from_dict(r['candidate']),memory)
        audit=verify_exclusion(c,2)
        if not audit['verified']: raise ArithmeticError('Baseline final exclusion failed')
        if r['bounds'].get('witness') and not verify_witness(c.to_dict(),r['bounds']['witness'])['verified']:
            raise ArithmeticError('Baseline witness failed')
        result['independent_final_audits'].append({'architecture_id':r['architecture_id'],**audit})
    result['distance_conditioned_frontiers']=tiers(result['records'])
    return result


def write_run(name,fn):
    path=OUT/'raw'/f'{name}.json.gz'
    if path.exists(): return
    start=time.perf_counter(); result=fn()
    result['driver_wall_seconds']=time.perf_counter()-start
    result['experiment_freeze_sha256']=sha256((OUT/'experiment_freeze.json').read_bytes()).hexdigest()
    path.parent.mkdir(parents=True,exist_ok=True)
    with gzip.open(path,'wt',encoding='utf-8') as f: json.dump(result,f,allow_nan=False)
    summary=result.get('resource_summary',result.get('summary'))
    print(name, summary['target_reached'], summary['minima_at_target'],round(result['driver_wall_seconds'],2),flush=True)


def run_primary():
    assert_frozen()
    for task in tasks():
        code=StabilizerCode.from_dict(json.loads((ROOT/task['code_path']).read_text()))
        memory=MemoryConfig(basis=task['basis'])
        for seed in SEEDS:
            for variant in ('v03','v04','resource','random','no_basis','no_family'):
                name=f'primary--{task["task"]}--{variant}--{seed}'
                cfg=ResourceConfig(seed=seed,basis_search=variant!='no_basis',new_family=variant!='no_family')
                write_run(name,lambda v=variant,cfg=cfg: baseline_result(code,memory,v,seed) if v in ('v03','resource','random')
                          else run_resource_search(code,memory,cfg))


def starts(code,seed,kind):
    a=next(iter(generate(code,1,seed)))
    if kind=='overprotected':
        a=replace(a,syndrome_budget=len(a.orders),ancilla_assignment=tuple(range(len(a.orders))),parallelism=1,
            flag_intervals=tuple(((0,len(o)),(0,len(o))) for o in a.orders),terminal_repetitions=1)
    return Design(a)


def run_secondary():
    assert_frozen(); calibration=[]
    for task in [t for t in tasks() if t['task'] in ('steane7-X','affine15_k1-X','simplex15_k7-X')]:
        code=StabilizerCode.from_dict(json.loads((ROOT/task['code_path']).read_text())); memory=MemoryConfig(basis='X')
        for seed in SEEDS:
            for kind in ('overprotected','bare'):
                design=starts(code,seed,kind); rec,_=evaluate(code,design,memory)
                calibration.append({'task':task['task'],'seed':seed,'kind':kind,'initial':rec})
                # Overprotected failure is reported, never silently replaced.
                if kind=='overprotected' and rec['region']!='VALID':
                    print('EXCLUDED_INVALID_OVERPROTECTED',task['task'],seed,flush=True); continue
                for variant in ('repair_only','repair_compress'):
                    name=f'{kind}--{task["task"]}--{variant}--{seed}'
                    cfg=ResourceConfig(seed=seed,initial_population=1,strategy=variant)
                    write_run(name,lambda cfg=cfg,d=design:run_resource_search(code,memory,cfg,[d]))
    dump(OUT/'secondary_starts.json',calibration)


def audit():
    assert_frozen(); paths=sorted((OUT/'raw').glob('*.json.gz')); audits=[]
    # Every unique final Pareto design is audited, not a cherry-picked best scalar.
    for p in paths:
        if any(f'--{v}--' in p.name for v in ('v03','random','resource')): continue
        with gzip.open(p,'rt',encoding='utf-8') as f: result=json.load(f)
        code=StabilizerCode.from_dict(result['code']); memory=MemoryConfig(**result['memory_configuration'])
        cfg=ResourceConfig(**result['configuration'])
        final={r['architecture_id']:r for r in result['records'] if r['architecture_id'] in result['frontier']}
        out=OUT/'minimality'/p.name
        if out.exists(): continue
        rows=[protection_audit(code,Design.from_dict(r['design']),memory,cfg) for r in final.values()]
        out.parent.mkdir(parents=True,exist_ok=True)
        with gzip.open(out,'wt',encoding='utf-8') as f: json.dump({'run':p.name,'audits':rows},f,allow_nan=False)
        print('minimality',p.name,len(rows),flush=True)
    dump(OUT/'raw_manifest.json',{p.relative_to(ROOT).as_posix():sha256(p.read_bytes()).hexdigest()
         for folder in ('raw','minimality') for p in sorted((OUT/folder).glob('*.gz'))})


if __name__=='__main__':
    parser=argparse.ArgumentParser(); parser.add_argument('action',choices=('freeze','primary','secondary','audit','verify'))
    action=parser.parse_args().action
    {'freeze':freeze,'primary':run_primary,'secondary':run_secondary,'audit':audit,'verify':assert_frozen}[action]()
