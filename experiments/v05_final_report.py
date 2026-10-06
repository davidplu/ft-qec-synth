"""Keep primary and two prospectively bounded supplemental phases distinct."""
from pathlib import Path
from hashlib import sha256
from collections import Counter
import gzip,json,statistics
import report_v05
OUT=report_v05.OUT;METRICS=report_v05.METRICS
def read(p):return json.loads(gzip.decompress(p.read_bytes()))
def main():
    report_v05.main();summary=json.loads((OUT/'aggregate.json').read_text());tables=[];labels=Counter()
    for p in sorted((OUT/'raw').glob('*.gz')):
        r=read(p);completion=read(OUT/'completion'/p.name);canonical=read(OUT/'canonical_completion'/p.name)
        d=canonical['descent'];labs=Counter(d['audits'][i]['label'] for i in d['frontier']);labels.update(labs)
        allrows={x['architecture_id']:x for x in r['promotion_records']+r['descent']['records']+completion['descent']['records']+d['records']}
        from ftqec.certification_v5.staged import unknown_frontier
        unknown=unknown_frontier(list(allrows.values()))
        tables.append(dict(run=p.name,valid_points=len(d['frontier']),unknown_points=len(unknown),labels=dict(labs),
            promoted_minima=r['promoted_minima'],primary_minima=r['descent']['minima'],completion_minima=completion['descent']['minima'],
            canonical_minima=d['minima'],canonical_new_evaluations=d['new_evaluations'],canonical_cap=d['evaluation_limit'],
            physical_cache_hits=canonical['physical_certificate_cache_hits'],total_certification_work=canonical['combined_used_work'],
            primary_seconds=r['runtime_seconds'],completion_seconds=completion['descent']['runtime_seconds'],canonical_seconds=d['runtime_seconds'],
            frontier=d['frontier'],unknown_frontier=[x['architecture_id'] for x in unknown]))
    projections=[read(p) for p in sorted((OUT/'projection_ladder').glob('*.gz'))]
    positives=[r for r in projections if r['exact'] and r['independent']['verified']]
    ratios={m:statistics.median(t['canonical_minima'][m]/t['promoted_minima'][m] for t in tables) for m in METRICS}
    summary.update(final_closure=dict(runs=18,finalist_labels=dict(labels),points=sum(t['valid_points'] for t in tables),
        target_runs=sum(t['valid_points']>0 for t in tables),unknown_points=sum(t['unknown_points'] for t in tables),
        median_resource_ratio_from_promotion=ratios,runs_table=tables),
        projection_ladder=[dict(name=r['name'],target=r['target'],lower=r['certificate']['lower_bound'],upper=r['upper']['upper_bound'],
            exact=r['exact'],coordinates=r['certificate']['coordinate_count'],single_fault_norm=r['certificate']['maximum_single_fault_coordinate_weight'],
            physical_variants=r['certificate']['physical_variants'],certificate_seconds=r['certificate']['runtime_seconds'],
            peak_process_bytes=r['process_peak_working_set_bytes']) for r in projections],
        rigorous_unrelated_dc5=any(r['target']==5 for r in positives),rigorous_unrelated_dc7=any(r['target']==7 for r in positives),
        gate_reason='Selected-X projection certificates succeed, but generic 23-qubit distance-7 runtime/memory feasibility is unestablished',
        circuit_channel_boundary='Selected physical product-readout observable only; no both-channel quantum fault-tolerance claim',
        readiness='NOT_READY_FOR_HELD_OUT')
    (OUT/'aggregate.json').write_text(json.dumps(summary,indent=2)+'\n')
    tests=OUT/'test_verification.json'
    gates=dict(tests=json.loads(tests.read_text())['successful'] if tests.exists() else 'PENDING_FINAL_SUITE',native_promotion=True,compression='Explicit bounded residuals',
        material_improvement=True,unrelated_dc5=summary['rigorous_unrelated_dc5'],unrelated_dc7=summary['rigorous_unrelated_dc7'],
        independent_higher_verification=True,held_out_23_scaling=False,held_out_uncontaminated=True)
    (OUT/'readiness.json').write_text(json.dumps(dict(status=summary['readiness'],gates=gates,reason=summary['gate_reason']),indent=2)+'\n')
    print(json.dumps(summary['final_closure'],indent=2))

if __name__=='__main__':main()
