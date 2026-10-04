"""Controlled, development-only search ablation and signature profiling."""
import argparse
from collections import defaultdict
import cProfile
import json
from pathlib import Path
import pstats
import statistics
import time
from ftqec.codes.stabilizer import StabilizerCode
from ftqec.architectures.generators import generate
from ftqec.circuits.memory import MemoryConfig, build_memory
from ftqec.search.cegis import SearchConfig, run_search
from ftqec.faults.signatures import signatures


def dump(path, value):
    path.write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8')


def aggregate(runs):
    groups = defaultdict(list)
    repairs = defaultdict(list)
    for entry in runs:
        result = entry['result']
        key = (entry['code'], result['memory_configuration']['basis'], result['configuration']['strategy'])
        groups[key].append(result)
        for rec in result['records']:
            if 'repair_outcome' in rec:
                p = rec['provenance']
                repairs[(p['failure_class'], p['repair_operator'])].append(rec['repair_outcome'])
    rows = []
    for (code, basis, strategy), values in sorted(groups.items()):
        reached = [r for r in values if r['summary']['target_reached']]
        rows.append({'code': code, 'basis': basis, 'strategy': strategy, 'seeds': len(values),
                     'target_reach_fraction': len(reached)/len(values),
                     'best_dc_lower_bounds': [r['summary']['best_dc_lower_bound'] for r in values],
                     'mean_best_dc_lower_bound': statistics.mean(r['summary']['best_dc_lower_bound'] for r in values),
                     'evaluations_to_target': [r['summary']['evaluations_to_target_dc'] for r in values],
                     'median_evaluations_to_target_conditional': statistics.median(r['summary']['evaluations_to_target_dc'] for r in reached) if reached else None,
                     'best_QD_at_target': [r['summary']['best_QD_at_target_dc'] for r in values],
                     'mean_wall_seconds': statistics.mean(r['runtime_seconds'] for r in values),
                     'unique_candidates': [r['unique_candidates_evaluated'] for r in values],
                     'incomplete_screens': sum(rec['bounds'].get('reason') == 'work_limit' for r in values for rec in r['records'])})
    repair_rows = []
    for (cls, operator), outcomes in sorted(repairs.items()):
        comparable = [o for o in outcomes if o['eliminates_source_witness'] is not None]
        repair_rows.append({'failure_class': cls, 'operator': operator, 'repairs': len(outcomes),
                            'successes': sum(o['repair_success'] for o in outcomes),
                            'success_rate': sum(o['repair_success'] for o in outcomes)/len(outcomes),
                            'transportable_witnesses': len(comparable),
                            'elimination_rate': sum(o['eliminates_source_witness'] for o in comparable)/len(comparable) if comparable else None,
                            'equal_or_worse_witnesses': sum(o['equal_or_worse_witness'] for o in outcomes)})
    return rows, repair_rows


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--budget', type=int, default=24)
    parser.add_argument('--seeds', type=int, nargs='+', default=[0, 1, 2])
    parser.add_argument('--rounds', type=int, default=3)
    parser.add_argument('--max-combinations', type=int, default=200000)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    out = root / 'results/v0.2'; raw = out / 'raw'; raw.mkdir(parents=True, exist_ok=True)
    runs = []; progress = []; profiler = cProfile.Profile()
    for name in ('css4', 'noncss4', 'perfect5', 'steane'):
        code = StabilizerCode.from_dict(json.loads((root/f'benchmarks/development/{name}.json').read_text(encoding='utf-8')))
        for basis in ('X', 'Z'):
            for seed in args.seeds:
                initial_ids = None
                for strategy in ('random', 'resource', 'cegis', 'mixed'):
                    memory = MemoryConfig(args.rounds, basis)
                    config = SearchConfig(budget=args.budget, seed=seed, strategy=strategy,
                                          max_combinations=args.max_combinations)
                    # Profile one representative run, not the controlled comparison.
                    result = run_search(code, memory, config)
                    if initial_ids is None: initial_ids = result['initial_population_ids']
                    assert result['initial_population_ids'] == initial_ids
                    assert result['evaluation_slots'] == args.budget
                    assert result['mutation_count'] == args.budget-min(6, args.budget)
                    filename = f'{name}-{basis}-seed{seed}-{strategy}.json'
                    dump(raw / filename, result)
                    runs.append({'code': name, 'file': filename, 'result': result})
                    p = {'code': name, 'basis': basis, 'seed': seed, 'strategy': strategy,
                         'best_dc': result['summary']['best_dc_lower_bound'],
                         'target_reached': result['summary']['target_reached'],
                         'runtime_seconds': result['runtime_seconds']}
                    progress.append(p); dump(out/'progress.json', progress)
                    print(json.dumps(p), flush=True)
    aggregate_rows, repair_rows = aggregate(runs)
    dump(out/'aggregate.json', aggregate_rows); dump(out/'repair_statistics.json', repair_rows)
    paired = []
    for name in ('css4','noncss4','perfect5','steane'):
        for basis in ('X','Z'):
            for seed in args.seeds:
                pair = {r['result']['configuration']['strategy']: r['result']['summary'] for r in runs
                        if r['code']==name and r['result']['memory_configuration']['basis']==basis and r['result']['seed']==seed}
                paired.append({'code':name,'basis':basis,'seed':seed,
                               'cegis_minus_random_dc':pair['cegis']['best_dc_lower_bound']-pair['random']['best_dc_lower_bound'],
                               'random_target_reached':pair['random']['target_reached'],'cegis_target_reached':pair['cegis']['target_reached'],
                               'random_evaluations_to_target':pair['random']['evaluations_to_target_dc'],
                               'cegis_evaluations_to_target':pair['cegis']['evaluations_to_target_dc']})
    dump(out/'paired_comparisons.json', paired)
    timings = []
    code = StabilizerCode.from_dict(json.loads((root/'benchmarks/development/steane.json').read_text(encoding='utf-8')))
    for candidate in generate(code, 3, 11):
        circuit = build_memory(code,candidate,MemoryConfig(args.rounds))
        before_times=[]; after_times=[]
        for _ in range(3):
            start=time.perf_counter(); before=signatures(circuit,backend='forward'); before_times.append(time.perf_counter()-start)
            start=time.perf_counter(); after=signatures(circuit); after_times.append(time.perf_counter()-start)
            assert before==after
        timings.append({'architecture_id':candidate.id,'operations':len(circuit.operations),'fault_variants':len(after),
                        'forward_seconds':before_times,'suffix_seconds':after_times,
                        'median_speedup':statistics.median(before_times)/statistics.median(after_times)})
    dump(out/'performance.json',timings)
    profiler.enable(); run_search(code,MemoryConfig(args.rounds),SearchConfig(budget=12,seed=11)); profiler.disable()
    profiler.dump_stats(str(out/'profile.pstats'))
    stats=pstats.Stats(profiler)
    profile_rows=[{'file':f,'line':l,'function':n,'calls':v[1],'self_seconds':v[2],'cumulative_seconds':v[3]}
                  for (f,l,n),v in stats.stats.items()]
    dump(out/'profile.json',sorted(profile_rows,key=lambda r:r['cumulative_seconds'],reverse=True)[:30])
    dump(out/'protocol.json',{'development_codes':['css4','noncss4','perfect5','steane'],
                             'rounds':args.rounds,'bases':['X','Z'],'seeds':args.seeds,'strategies':['random','resource','cegis','mixed'],
                             'evaluation_budget':args.budget,'mutation_count':max(0,args.budget-6),'initial_population':min(6,args.budget),
                             'target_dc':3,'max_weight':3,'beam_width':12,'decoder_weight':1,'logical_index':0,'max_flags_per_check':4,'max_combinations':args.max_combinations,'idles':False,
                             'noisy_input':False,'budget_policy':'every proposal including cached duplicates consumes one slot',
                             'total_runs':len(runs),'total_evaluation_slots':sum(r['result']['evaluation_slots'] for r in runs),
                             'total_wall_seconds':sum(r['result']['runtime_seconds'] for r in runs)})


if __name__=='__main__': main()
