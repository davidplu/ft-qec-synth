"""Aggregate raw endpoint replay without mixing native, promotion and descent gains."""
from pathlib import Path
from hashlib import sha256
from collections import Counter
import gzip,json,statistics

ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'results/v0.5'
METRICS=('Q','D','QD','two_q_gates')


def main():
    files=sorted((OUT/'raw').glob('*.json.gz'))
    if len(files)!=18:raise ValueError(f'Expected all 18 frozen V0.4 primary traces, got {len(files)}')
    runs=[json.loads(gzip.decompress(p.read_bytes())) for p in files]
    labels=Counter();tables=[]
    for p,r in zip(files,runs):
        final=r['descent']['frontier']
        labs=Counter(r['descent']['audits'][i]['label'] for i in final);labels.update(labs)
        tables.append(dict(run=p.name,native_points=len(r['native_frontier']),promoted_points=len(r['promoted_frontier']),
            final_points=len(final),labels=dict(labs),unknown_points=len(r['unknown_pareto']),
            native_minima=r['native_minima'],promoted_minima=r['promoted_minima'],final_minima=r['descent']['minima'],
            runtime_seconds=r['runtime_seconds'],new_descent_evaluations=r['descent']['new_evaluations'],
            certification_work=r['certification_budget']['used'],promotion_work=r['promotion_work'],
            descent_budget_stopped=r['descent']['stopped_by_budget']))
    ladder=json.loads(gzip.decompress((OUT/'ladder.json.gz').read_bytes()))
    sufficient5=any(r['target']==5 and r['readiness_eligible'] for r in ladder)
    sufficient7=any(r['target']==7 and r['readiness_eligible'] for r in ladder)
    comparisons={}
    for before,after in [('native_minima','promoted_minima'),('promoted_minima','final_minima')]:
        comparisons[f'{before}__{after}']={m:dict(pairs=sum(t[before][m] is not None and t[after][m] is not None for t in tables),
            median_ratio=statistics.median([t[after][m]/t[before][m] for t in tables if t[before][m] and t[after][m] is not None]))
            for m in METRICS}
    summary=dict(runs=len(runs),native_target_runs=sum(bool(r['native_frontier']) for r in runs),
                 promoted_target_runs=sum(bool(r['promoted_frontier']) for r in runs),
                 final_target_runs=sum(bool(r['descent']['frontier']) for r in runs),
                 finalist_labels=dict(labels),unknown_frontier_points=sum(len(r['unknown_pareto']) for r in runs),
                 comparisons=comparisons,median_runtime_seconds=statistics.median(r['runtime_seconds'] for r in runs),
                 max_runtime_seconds=max(r['runtime_seconds'] for r in runs),runs_table=tables,
                 raw_hashes={p.relative_to(ROOT).as_posix():sha256(p.read_bytes()).hexdigest() for p in files},
                 readiness='NOT_READY_FOR_HELD_OUT',rigorous_unrelated_dc5=sufficient5,rigorous_unrelated_dc7=sufficient7,
                 gate_reason='No independently verified meaningful unrelated distance-5/7 quantum-memory demonstration',
                 circuit_channel_boundary='Repetition channels do not count: full quantum code distance 1')
    (OUT/'aggregate.json').write_text(json.dumps(summary,indent=2)+'\n')
    (OUT/'readiness.json').write_text(json.dumps({k:summary[k] for k in ('readiness','rigorous_unrelated_dc5','rigorous_unrelated_dc7','gate_reason')},indent=2)+'\n')
    print(json.dumps({k:summary[k] for k in ('runs','native_target_runs','promoted_target_runs','final_target_runs','finalist_labels','median_runtime_seconds','readiness')},indent=2))


if __name__=='__main__':main()
