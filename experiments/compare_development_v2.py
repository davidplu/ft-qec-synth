"""Prospectively frozen matched experiment and conservative seed-block tests."""
from collections import defaultdict,Counter
from dataclasses import replace,asdict
from itertools import product
import argparse
import gzip
import json
import math
import random
import statistics
import time
import ctypes
from pathlib import Path
from development_v2 import ROOT,OUT,BENCH,dump,sha,assert_frozen
from ftqec.codes.stabilizer import StabilizerCode
from ftqec.search.malignant import MalignantConfig,run_malignant_search
from ftqec.circuits.memory import MemoryConfig,build_memory
from ftqec.architectures.candidate import Candidate
from ftqec.faults.verification import verify_witness
from ftqec.faults.exclusion import verify_exclusion
from ftqec.faults.signatures import signatures
from ftqec.faults.spectrum import representative_witness
from ftqec.faults.batch_verification import replay_lanes

VARIANTS={'random':{},'resource':{},'v02':{},'v03':{},'mixed':{},
          'v03_raw':{'equivalence':'raw'},'v03_signature':{'equivalence':'signature'},
          'v03_no_protection':{'protect_progress':False},'v03_arbitrary':{'dominant_order':False},
          'v03_no_coverage':{'coverage_priority':False}}

def rss():
    if hasattr(ctypes,'windll'):
        class Counters(ctypes.Structure):
            _fields_=[('cb',ctypes.c_ulong),('faults',ctypes.c_ulong)]+[(n,ctypes.c_size_t) for n in ('peak','working','peakpaged','paged','peaknonpaged','nonpaged','pagefile','peakpagefile')]
        p=Counters();p.cb=ctypes.sizeof(p)
        get=ctypes.windll.psapi.GetProcessMemoryInfo
        get.argtypes=[ctypes.c_void_p,ctypes.c_void_p,ctypes.c_ulong]
        ctypes.windll.kernel32.GetCurrentProcess.restype=ctypes.c_void_p
        if not get(ctypes.windll.kernel32.GetCurrentProcess(),ctypes.byref(p),p.cb):raise ctypes.WinError()
        return {'working_set_bytes':p.working,'peak_working_set_bytes':p.peak}
    return {}

def manifest():
    assert_frozen();screen=json.loads((OUT/'screening.json').read_text());pilots={p['task']:p for p in json.loads((OUT/'pilots.json').read_text())}
    additional={p['task']:p for p in json.loads((OUT/'additional_reachability.json').read_text())}
    role={p['task']:p for p in json.loads((OUT/'role_reachability.json').read_text())}
    for task,p in pilots.items():
        if additional.get(task,{}).get('reachable'):
            p['reachable']=True;p['status']='CONSTRUCTIVELY_REACHABLE_WITH_GENERIC_SPLIT_FLAGS'
        if role.get(task,{}).get('reachable'):
            p['reachable']=True;p['status']='CONSTRUCTIVELY_REACHABLE_WITH_GENERIC_READOUT_ROLE_FLAGS'
    eligible=[s for s in screen if s['classification']=='OPEN_HEADROOM' and s['difficulty']=='USEFUL'
              and s['task'] in pilots and pilots[s['task']]['reachable'] and pilots[s['task']]['target']==s['d_target']]
    # Round-robin construction families, then code instances; paired bases do
    # not displace an unrepresented code. Generator controls share their parent.
    families=defaultdict(list)
    for s in eligible:families[s['family']].append(s)
    ordered=[]
    for family,items in sorted(families.items()):
        names=sorted({s['name'] for s in items},key=lambda n:(next(s['shared_parent'] is not None for s in items if s['name']==n),next(s['n'] for s in items if s['name']==n),n))
        families[family]=[next(s for s in items if s['name']==name and s['basis']==basis) for basis in ('X','Z') for name in names if any(s['name']==name and s['basis']==basis for s in items)]
    while any(families.values()):
        for family in sorted(families):
            if families[family]:ordered.append(families[family].pop(0))
    selected=ordered[:8]
    pool={r['name']:r for r in json.loads((OUT/'candidate_pool.json').read_text())}
    tasks=[]
    for s in selected:
        info=pool[s['name']];metrics=info['metrics'];runs=s['calibration_runs']
        tasks.append({**{k:v for k,v in s.items() if k!='calibration_runs'},'metrics':metrics,
            'provenance':json.loads((ROOT/s['code_path']).read_text())['provenance'],
            'code_file_sha256':sha(ROOT/s['code_path']),
            'initial_malignant_spectra':[r['spectra'] for r in runs],
            'initial_population_ids':[r['initial_ids'] for r in runs],
            'calibration_seeds':[0,1,2], 'reachability':pilots[s['task']]['status'],
            'inclusion_reason':'Independently proved boundary headroom, zero calibrated initial target successes, and a certified development-only target witness; strategy-blind family round robin.'})
    m={'suite':'Development Suite 2','permanent_development':True,'algorithm_commit':assert_frozen(),
       'selection_protocol':'docs/DEVELOPMENT_V2_SELECTION_PROTOCOL.md','tasks':tasks,
       'final_seeds':list(range(10,20)),'evaluation_budget':32,
       'configuration':asdict(MalignantConfig()),'primary_variants':list(VARIANTS)[:5],
       'secondary_ablation_seeds':[10,11,12],'secondary_ablations':list(VARIANTS)[5:],
       'held_out_inputs_accessed':False,'selection_uses_v03_outcomes':False,
       'reserved_unexecuted_families':['quaternary quadratic-residue input pending validation','five-qubit concatenation','periodic toric distance five']}
    dump(BENCH/'MANIFEST.json',m)
    protocol={'manifest_sha256':sha(BENCH/'MANIFEST.json'),'algorithm_commit':assert_frozen(),
              'hypothesis_sha256':sha(ROOT/'docs/DEVELOPMENT_V2_HYPOTHESIS.md'),
              'selection_protocol_sha256':sha(ROOT/'docs/DEVELOPMENT_V2_SELECTION_PROTOCOL.md'),
              'pool_extension_sha256':sha(ROOT/'docs/DEVELOPMENT_V2_POOL_EXTENSION.md'),
              'pilot_extension_sha256':sha(ROOT/'docs/DEVELOPMENT_V2_PILOT_EXTENSION.md'),
              'role_pilot_sha256':sha(ROOT/'docs/DEVELOPMENT_V2_ROLE_PILOT.md')}
    dump(OUT/'protocol.json',protocol)
    lines=['# Development Suite 2','',f"{len(tasks)} primary code/basis tasks selected from {len(pool)} code instances. All are permanently development inputs. Shared parents and basis tasks are not independent families.",'',
           '| Task | n | k | CSS generators | d code | initial | boundary | target |',
           '|---|---:|---:|---|---:|---:|---:|---:|']
    for s in tasks:
        d=s['distance_certificate'];lines.append(f"| {s['task']} | {s['n']} | {s['k']} | {s['css']} | {d.get('construction_distance',d.get('distance',d.get('lower_bound')))} | {s['d_initial']} | {s['boundary']['distance']} | {s['d_target']} |")
    lines+=['','The manifest includes full check weights, qubit degrees, overlap matrices, spectrum calibration and provenance. Mechanism coverage is a deterministic representative sample, not an exhaustive absence test. The Shor row/column distance argument and exhaustive code-distance results are retained in candidate_pool.json. Non-CSS generator controls represent an existing CSS stabilizer group, not a genuinely different construction.','',
            'Final comparison: ten new seeds (10–19), 32 evaluations per arm following the documented pre-comparison compute amendment, fixed 200000 certification/spectrum caps and all other frozen V0.3 parameters. Ablations are secondary three-seed comparisons. Pilots use only random/resource arms (seeds 6,7) plus predetermined fully flagged constructions. No pilot candidate is supplied to final initial populations.','',
            'Rejected and deferred tasks:', '', '| Task | Screen | Difficulty | Pilot |','|---|---|---|---|']
    for s in screen:
        if s['task'] not in {t['task'] for t in tasks}:lines.append(f"| {s['task']} | {s['classification']} | {s['difficulty']} | {pilots.get(s['task'],{}).get('status','not eligible')} |")
    (ROOT/'docs/DEVELOPMENT_V2.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print(json.dumps({'tasks':[t['task'] for t in tasks],'manifest_sha256':protocol['manifest_sha256']}))

def check_protocol():
    assert_frozen();p=json.loads((OUT/'protocol.json').read_text())
    assert p['manifest_sha256']==sha(BENCH/'MANIFEST.json')
    assert p['hypothesis_sha256']==sha(ROOT/'docs/DEVELOPMENT_V2_HYPOTHESIS.md')
    assert p['selection_protocol_sha256']==sha(ROOT/'docs/DEVELOPMENT_V2_SELECTION_PROTOCOL.md')
    assert p['pool_extension_sha256']==sha(ROOT/'docs/DEVELOPMENT_V2_POOL_EXTENSION.md')
    assert p['pilot_extension_sha256']==sha(ROOT/'docs/DEVELOPMENT_V2_PILOT_EXTENSION.md')
    assert p['role_pilot_sha256']==sha(ROOT/'docs/DEVELOPMENT_V2_ROLE_PILOT.md')
    m=json.loads((BENCH/'MANIFEST.json').read_text())
    for t in m['tasks']:assert t['code_file_sha256']==sha(ROOT/t['code_path'])
    return m

def run():
    m=check_protocol();raw=OUT/'raw';raw.mkdir(exist_ok=True);rows=[];started=time.perf_counter()
    for t in m['tasks']:
        code=StabilizerCode.from_dict(json.loads((ROOT/t['code_path']).read_text()))
        for seed in m['final_seeds']:
            initial=None
            for variant,changes in VARIANTS.items():
                if variant not in m['primary_variants'] and seed not in m['secondary_ablation_seeds']:continue
                path=raw/f"{t['task']}-seed{seed}-{variant}.json.gz"
                if path.exists():
                    with gzip.open(path,'rt',encoding='utf-8') as f:result=json.load(f)
                else:
                    config=replace(MalignantConfig(),budget=m['evaluation_budget'],seed=seed,target_dc=t['d_target'],
                        strategy=variant if variant in m['primary_variants'] else 'v03',**changes)
                    before=time.perf_counter();result=run_malignant_search(code,MemoryConfig(3,t['basis']),config)
                    result['experiment_wall_seconds']=time.perf_counter()-before
                    result['process_memory']=rss();result['development_task']=t['task'];result['experiment_variant']=variant
                    result['benchmark_manifest_sha256']=sha(BENCH/'MANIFEST.json')
                    result['frozen_algorithm_commit']=m['algorithm_commit']
                    with gzip.open(path,'wt',encoding='utf-8',compresslevel=6) as f:json.dump(result,f,separators=(',',':'),allow_nan=False)
                assert result['evaluation_slots']==m['evaluation_budget']
                assert result['configuration']['seed']==seed
                if initial is not None:assert result['initial_population_ids']==initial
                initial=result['initial_population_ids']
                row={'task':t['task'],'code':t['name'],'family':t['family'],'seed':seed,'variant':variant,
                     'target':result['summary']['target_reached'],'best_dc':result['summary']['best_dc_lower_bound'],
                     'target_evaluations':result['summary']['evaluations_to_target'],
                     'seconds':result['runtime_seconds'],'file':path.name}
                rows.append(row);dump(OUT/'progress.json',rows);print(json.dumps(row),flush=True)
    dump(OUT/'timing.json',{'runs':len(rows),'slots':len(rows)*m['evaluation_budget'],
         'driver_wall_seconds':time.perf_counter()-started,'sum_search_seconds':sum(r['seconds'] for r in rows)})
    dump(OUT/'raw_manifest.json',[{'file':p.relative_to(ROOT).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(raw.glob('*.gz'))])
    assert_frozen()

def sign_permutation(values):
    values=[v for v in values if abs(v)>1e-12]
    if not values:return 1.0
    observed=abs(sum(values));return sum(abs(sum(s*v for s,v in zip(signs,values)))>=observed-1e-10 for signs in product((-1,1),repeat=len(values)))/(2**len(values))

def holm(tests):
    last=0
    for j,t in enumerate(sorted(tests,key=lambda t:t['p'])):
        last=max(last,min(1,(len(tests)-j)*t['p']));t['p_holm']=last

def audit():
    m=check_protocol();tasks={t['task']:t for t in m['tasks']};seen=set();counts=Counter();details=[];initial_quality={};initial_rows={}
    from jsonschema import Draft202012Validator
    validator=Draft202012Validator(json.loads((ROOT/'docs/schemas/result-v0.3.schema.json').read_text()))
    # Architecture-local deduplication; no search result can grant a certificate.
    for i,path in enumerate(sorted((OUT/'raw').glob('*.gz'))):
        with gzip.open(path,'rt',encoding='utf-8') as f:r=json.load(f)
        validator.validate(r)
        t=tasks[r['development_task']];code=StabilizerCode.from_dict(r['code'])
        for rec in r['records']:
            key=(t['task'],rec['architecture_id'])
            if key in seen:continue
            seen.add(key);c=build_memory(code,Candidate.from_dict(rec['candidate']),MemoryConfig(3,t['basis']))
            b=rec['bounds']
            if b.get('witness'):
                assert verify_witness(c,b['witness'])['verified'];counts['minimum_witnesses']+=1
            if b['lower_bound']>1:
                cert=verify_exclusion(c,b['lower_bound']-1);assert cert['verified'];counts['nontrivial_exclusions']+=1
            ss=signatures(c);classes=rec['malignant_spectrum']['classes']
            for weight,layer in rec['malignant_spectrum']['layers'].items():
                if layer['complete']:
                    native=[cls for cls in classes if cls['weight']==int(weight)]
                    assert layer['class_count']==len(native)
                    assert layer['raw_count']==sum(layer['multiplicities'].values())
                else:assert layer['class_count'] is None
            for start in range(0,len(classes),1024):
                ws=[representative_witness(c,ss,cls) for cls in classes[start:start+1024]]
                actual=replay_lanes(c,[w['faults'] for w in ws])
                for w,a in zip(ws,actual):
                    for field in ('detector_outcomes','logical_coset','flag_outcomes','final_data_pauli'):assert a[field]==w[field]
                    assert a['detector_outcomes']==0 and a['logical_coset'];counts['class_representatives']+=1
            counts['architectures']+=1
        for rec in r['records'][:6]:
            key=(t['task'],rec['architecture_id']);b=rec['bounds']
            if key not in initial_quality:
                if b['lower_bound']>=t['d_target']:quality={'target':True,'method':'native bound independently excluded'}
                elif b['upper_bound'] is not None:quality={'target':False,'method':'independently replayed below-target witness'}
                else:
                    c=build_memory(code,Candidate.from_dict(rec['candidate']),MemoryConfig(3,t['basis']))
                    certificate=verify_exclusion(c,t['d_target']-1)
                    quality={'target':certificate['verified'],'method':'independent resolution of native cap','exclusion':certificate}
                initial_quality[key]=quality
            rowkey=(t['task'],r['configuration']['seed'],rec['evaluation_index'])
            initial_rows[rowkey]={'task':t['task'],'seed':r['configuration']['seed'],'node':rec['evaluation_index'],
                'architecture_id':rec['architecture_id'],'native_lower_bound':b['lower_bound'],**initial_quality[key]}
        for rec in r['records']:
            if rec.get('dc_delta',0)>0:
                assert rec['independent_exclusion']['verified'];counts['gain_events']+=1
                details.append({'file':path.name,'gain_node':rec['evaluation_index'],'parent_node':rec['parent_node'],
                    'class_eliminated_by_global_exclusion':True,
                    'source_transport_status':rec.get('repair_outcome_v03',{}).get('transported_source_class_eliminated'),
                    'reason':'independent exclusion eliminates every valid lower-tier fault set in the new physical circuit; semantic transport recorded separately'})
        print(json.dumps({'audit_run':i+1,'counts':dict(counts)}),flush=True)
        dump(OUT/'audit_progress.json',{'runs':i+1,'counts':dict(counts)})
    dump(OUT/'validation.json',{'verified':True,'counts':dict(counts),'distance_gains':details,
                              'algorithm_unchanged':True,'previous_results_unchanged':True,'held_out_runs':0})
    dump(OUT/'final_initial_quality.json',list(initial_rows.values()))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('stage',choices=('manifest','run','audit'));a=p.parse_args()
    {'manifest':manifest,'run':run,'audit':audit}[a.stage]()
