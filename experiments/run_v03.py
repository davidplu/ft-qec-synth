"""Frozen V0.3 development experiment; never reads held-out inputs or V0.2 raw."""
import cProfile
from dataclasses import replace
import gzip
import hashlib
import json
from pathlib import Path
import time
from ftqec.codes.stabilizer import StabilizerCode
from ftqec.circuits.memory import MemoryConfig
from ftqec.search.malignant import MalignantConfig, run_malignant_search

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'results/v0.3'
VARIANTS = {
    'random': {}, 'resource': {}, 'v02': {}, 'v03': {}, 'mixed': {},
    'v03_raw': {'equivalence':'raw'},
    'v03_signature': {'equivalence':'signature'},
    'v03_no_protection': {'protect_progress':False},
    'v03_arbitrary': {'dominant_order':False},
    'v03_no_coverage': {'coverage_priority':False}}


def main():
    OUT.mkdir(parents=True,exist_ok=True); (OUT/'raw').mkdir(exist_ok=True)
    hypothesis = (ROOT/'docs/V0_3_HYPOTHESIS.md').read_bytes()
    protocol = {'baseline_commit':'e6e9c746151552befa4105a3b02b30a1d4a5b2c9',
        'hypothesis_sha256':hashlib.sha256(hypothesis).hexdigest(),
        'codes':['css4','noncss4','perfect5','steane'],'bases':['X','Z'],'seeds':list(range(6)),
        'variants':VARIANTS,'configuration':MalignantConfig().__dict__,
        'raw_format':'gzip-compressed JSON, lossless; validate after decompression',
        'held_out_runs':0,'external_architecture_searches':0}
    (OUT/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n',encoding='utf-8')
    progress=[];started=time.perf_counter()
    for name in protocol['codes']:
        code=StabilizerCode.from_dict(json.loads((ROOT/f'benchmarks/development/{name}.json').read_text(encoding='utf-8')))
        for basis in protocol['bases']:
            for seed in protocol['seeds']:
                initial=None
                for variant,changes in VARIANTS.items():
                    config=replace(MalignantConfig(),seed=seed,strategy=variant if variant in ('random','resource','v02','v03','mixed') else 'v03',**changes)
                    result=run_malignant_search(code,MemoryConfig(3,basis),config)
                    if initial is None:initial=result['initial_population_ids']
                    assert result['initial_population_ids']==initial
                    assert result['evaluation_slots']==32 and result['mutation_count']==26
                    result['experiment_variant']=variant;result['development_code']=name
                    filename=f'{name}-{basis}-seed{seed}-{variant}.json.gz'
                    with gzip.open(OUT/'raw'/filename,'wt',encoding='utf-8',compresslevel=6) as stream:
                        json.dump(result,stream,separators=(',',':'),allow_nan=False)
                    row={'code':name,'basis':basis,'seed':seed,'variant':variant,'file':filename,
                        'best_dc':result['summary']['best_dc_lower_bound'],'target':result['summary']['target_reached'],
                        'compositions':result['summary']['successful_compositions'],'seconds':result['runtime_seconds']}
                    progress.append(row);print(json.dumps(row),flush=True)
                    (OUT/'progress.json').write_text(json.dumps(progress,indent=2)+'\n',encoding='utf-8')
    (OUT/'timing.json').write_text(json.dumps({'runs':len(progress),'slots':len(progress)*32,'wall_seconds':time.perf_counter()-started,
        'sum_search_seconds':sum(p['seconds'] for p in progress)},indent=2)+'\n',encoding='utf-8')
    # Profiling is separate, excluded from matched comparison timing.
    profiler=cProfile.Profile();profiler.enable()
    run_malignant_search(code,MemoryConfig(3,'Z'),replace(MalignantConfig(),budget=8))
    profiler.disable()
    import pstats
    stats=pstats.Stats(profiler)
    rows=sorted([{'function':f'{k[0]}:{k[1]}:{k[2]}','calls':v[1],'self_seconds':v[2],'cumulative_seconds':v[3]} for k,v in stats.stats.items()],key=lambda r:r['cumulative_seconds'],reverse=True)[:30]
    (OUT/'profile.json').write_text(json.dumps(rows,indent=2)+'\n',encoding='utf-8')


if __name__=='__main__': main()
