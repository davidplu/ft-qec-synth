"""Validate the saved pilot, replay its witnesses, and write the research report."""
from collections import defaultdict
import json
from pathlib import Path
import statistics
import jsonschema
from ftqec.codes.stabilizer import StabilizerCode
from ftqec.architectures.candidate import Candidate
from ftqec.circuits.memory import MemoryConfig, build_memory
from ftqec.faults.verification import verify_witness


def main():
    root = Path(__file__).resolve().parents[1]
    out = root / 'results/v0.2'
    protocol = json.loads((out/'protocol.json').read_text(encoding='utf-8'))
    aggregate = json.loads((out/'aggregate.json').read_text(encoding='utf-8'))
    paired = json.loads((out/'paired_comparisons.json').read_text(encoding='utf-8'))
    repairs = json.loads((out/'repair_statistics.json').read_text(encoding='utf-8'))
    performance = json.loads((out/'performance.json').read_text(encoding='utf-8'))
    verification = json.loads((out/'verification.json').read_text(encoding='utf-8'))
    validator = jsonschema.Draft202012Validator(json.loads((root/'docs/schemas/result-v0.2.schema.json').read_text(encoding='utf-8')))
    runs = []; replayed = 0; successful = []; eliminated_only = []; target_records = []
    local_counts = defaultdict(int); initial_only = True
    for file in sorted((out/'raw').glob('*.json')):
        run = json.loads(file.read_text(encoding='utf-8')); validator.validate(run)
        assert run['evaluation_slots'] == protocol['evaluation_budget']
        assert run['mutation_count'] == protocol['mutation_count']
        code = StabilizerCode.from_dict(run['code']); memory = MemoryConfig(**run['memory_configuration'])
        records = {r['architecture_id']: r for r in run['records']}
        for r in run['records']:
            witness = r['bounds'].get('witness')
            if witness:
                circuit = build_memory(code, Candidate.from_dict(r['candidate']), memory)
                if not verify_witness(circuit.to_dict(), witness)['verified']:
                    raise ArithmeticError(f'Saved witness failed replay: {file.name}, {r["evaluation_index"]}')
                replayed += 1
            outcome = r.get('repair_outcome')
            if outcome:
                for key in ('raises_minimum_witness_weight','improves_distance_lower_bound',
                            'preserves_exact_distance_improves_resources','repair_success'):
                    local_counts[key] += bool(outcome[key])
                if outcome['eliminates_source_witness'] is not None:
                    local_counts['transportable'] += 1
                    local_counts['eliminated'] += bool(outcome['eliminates_source_witness'])
                local_counts['repairs'] += 1
                parent = records[r['provenance']['parent_id']]
                sample = (file.name, run, parent, r)
                if outcome['improves_distance_lower_bound']: successful.append(sample)
                elif outcome['eliminates_source_witness'] and not outcome['repair_success']: eliminated_only.append(sample)
        reached = run['summary']['evaluations_to_target_dc']
        if reached:
            initial_only &= reached <= len(run['initial_population_ids'])
        target_records.extend((file.name, r) for r in run['frontier'])
        runs.append(run)
    assert len(runs) == protocol['total_runs']
    examples = out/'examples'; examples.mkdir(exist_ok=True)
    example_rows = []
    for label, samples in [('local-quality-repair',successful),('witness-only-repair',eliminated_only)]:
        if not samples: continue
        file, run, parent, child = samples[0]
        code = StabilizerCode.from_dict(run['code']); memory=MemoryConfig(**run['memory_configuration'])
        for name, rec in [('parent',parent),('child',child)]:
            c = build_memory(code,Candidate.from_dict(rec['candidate']),memory)
            (examples/f'{label}-{name}-circuit.json').write_text(json.dumps(c.to_dict(),indent=2)+'\n')
            (examples/f'{label}-{name}-witness.json').write_text(json.dumps(rec['bounds']['witness'],indent=2)+'\n')
        row={'label':label,'source_run':file,'parent_id':parent['architecture_id'],'child_id':child['architecture_id'],
             'provenance':child['provenance'],'outcome':child['repair_outcome'],
             'parent_bounds':parent['bounds'],'child_bounds':child['bounds'],
             'parent_resources':parent['resources'],'child_resources':child['resources']}
        (examples/f'{label}.json').write_text(json.dumps(row,indent=2)+'\n'); example_rows.append(row)
    quality_advantage = any(p['cegis_minus_random_dc'] > 0 for p in paired)
    gate = {'status':'NOT_READY_FOR_HELD_OUT',
            'correctness':{'tests_passed':verification['passed'],'tests_failed':verification['failures'],
                           'tests_skipped':verification['skipped'],'saved_witnesses_independently_replayed':replayed,
                           'raw_runs_schema_validated':len(runs),'dense_state_semantics_tested':True},
            'search':{'cegis_distance_wins':sum(p['cegis_minus_random_dc']>0 for p in paired),
                      'cegis_distance_ties':sum(p['cegis_minus_random_dc']==0 for p in paired),
                      'cegis_distance_losses':sum(p['cegis_minus_random_dc']<0 for p in paired),
                      'all_target_successes_reached_in_initial_population':initial_only,
                      'empirical_stronger_distance_advantage':quality_advantage,
                      'statistically_established_advantage':False},
            'performance':{'evaluation_slots':protocol['total_evaluation_slots'],
                           'wall_seconds':protocol['total_wall_seconds'],
                           'slots_per_second':protocol['total_evaluation_slots']/protocol['total_wall_seconds'],
                           'median_signature_speedup':statistics.median(r['median_speedup'] for r in performance),
                           'large_code_scaling_tested':False},
            'isolation':{'held_out_runs':0,'held_out_files':sorted(p.name for p in (root/'benchmarks/held_out').iterdir()),
                         'external_architecture_searches':0},
            'reasons':['No strongest-distance or target-reach advantage for CEGIS in this pilot.',
                       'Product-basis final readout limits the non-CSS memory experiments.',
                       'Three seeds and small budgets do not establish a general search-efficiency advantage.',
                       'Held-out-size throughput has not been measured.']}
    (out/'readiness.json').write_text(json.dumps(gate,indent=2)+'\n')
    (out/'validation.json').write_text(json.dumps({'raw_runs':len(runs),'schema_valid':True,
        'witnesses_replayed':replayed,'all_witnesses_verified':True,'local_repair_counts':dict(local_counts)},indent=2)+'\n')
    rows = ['# V0.2 research results', '', '**NOT_READY_FOR_HELD_OUT.** The repeated-memory implementation and independent checks pass, but this pilot does not support the claim that CEGIS reaches stronger architectures more efficiently than unguided search.', '',
            '## Baseline and exact changes', '',
            'V0.1 delivered source was not a Git repository. It was preserved as baseline commit `0291500da4c5977a093988f918c8baf8ffdf867e`; development uses branch `development/v0.2`. Packaging/serialization fixes were committed separately, with 34 passing baseline tests and zero skips. The original algebra, gadgets, candidates, scheduler and search were extended rather than replaced.', '',
            'V0.2 adds repeated rounds, temporal detectors and phase-correct compatible-stabilizer-subgroup readout closure; destructive X/Z logical memory readout; separate bounded minimum-weight decoder metrics; round/check/location metadata; backward packed transfer maps; independently replayed witnesses; structural analysis and generic repairs; mutation provenance; matched ablations; JSON-native public objects and mandatory complete dev dependencies. V0.1 ideal-boundary mode remains explicitly selectable.', '',
            '## Frozen protocol', '',
            f"Development inputs: css4, noncss4, perfect5 and Steane. Both X/Z memory at logical index 0; R={protocol['rounds']}; ideal encoded input; noisy ancilla resets, gates and readouts; physical terminal product readout; implicit idles and optional input noise disabled in this pilot. Maximum physical fault weight 3; {protocol['max_combinations']} work entries per search; target d_c >= 3.", '',
            f"Seeds {protocol['seeds']}; four strategies; six identical initial candidates; {protocol['evaluation_budget']} slots and {protocol['mutation_count']} mutation proposals per run. Duplicates consume slots with a common cache policy. {protocol['total_runs']} runs, {protocol['total_evaluation_slots']} slots, {protocol['total_wall_seconds']:.3f} summed wall seconds. Time is measured, not equalized. Exact model and limitations are in `FAULT_MODEL.md` and `V0_2_LIMITATIONS.md`.", '',
            '## Multi-seed distance comparison', '',
            'Each entry lists the best certified d_c lower bound at seeds 0, 1 and 2. Values are lower bounds, not assertions of exact distance.', '',
            '| Code | Memory | Random | Resource | CEGIS | Mixed |', '|---|---|---|---|---|---|']
    lookup = {(r['code'],r['basis'],r['strategy']):r for r in aggregate}
    for code in protocol['development_codes']:
        for basis in ('X','Z'):
            vals=[str(lookup[(code,basis,s)]['best_dc_lower_bounds']) for s in ('random','resource','cegis','mixed')]
            rows.append(f'| {code} | {basis} | '+' | '.join(vals)+' |')
    wins=gate['search']['cegis_distance_wins']; ties=gate['search']['cegis_distance_ties']; losses=gate['search']['cegis_distance_losses']
    rows += ['',f'CEGIS versus random: {wins} stronger-distance wins, {ties} ties and {losses} losses across the 24 paired code/basis/seed conditions. No strongest-distance improvement was observed. These cohorts share code structure and must not be pooled as independent statistical trials.', '',
             '## Target efficiency, ablations and resource frontiers', '',
             '| Strategy | Runs reaching target | Fraction | Mean seconds/run |', '|---|---:|---:|---:|']
    for strategy in ('random','resource','cegis','mixed'):
        group=[r for r in runs if r['configuration']['strategy']==strategy]
        successes=sum(r['summary']['target_reached'] for r in group)
        rows.append(f"| {strategy} | {successes}/{len(group)} | {successes/len(group):.3f} | {statistics.mean(r['runtime_seconds'] for r in group):.3f} |")
    rows += ['',f'All target successes occurred in the common initial population: {initial_only}. Accordingly, evaluations-to-target are not evidence of a guided-mutation benefit. Unreached targets remain in the reach-fraction denominator; target-conditioned timing/resource statistics remain explicitly conditional. Full per-seed first-tier evaluation/time and best Q/D/QD/2Q metrics are saved in every raw run and `aggregate.json`.', '',
             'Target-conditioned frontiers compare Q, D, QD and two-qubit gates separately after requiring the certified distance threshold. Most frontiers are empty, which is an experimental result rather than a missing export. Representative nonempty vectors:', '']
    for file,r in target_records[:8]:
        m=r['resources']; rows.append(f"- `{file}`, `{r['architecture_id']}`: Q={m['Q']}, D={m['D']}, QD={m['QD']}, 2Q={m['two_q_gates']}, bound={r['bounds']['status']} >= {r['bounds']['lower_bound']}.")
    rows += ['', '## Repairs and counterexamples', '',
             f"{local_counts['repairs']} guided repair proposals were evaluated. {local_counts['eliminated']}/{local_counts['transportable']} transportable source witnesses were eliminated. {local_counts['improves_distance_lower_bound']} proposals improved their parent's certified lower bound, and {local_counts['preserves_exact_distance_improves_resources']} preserved exact distance with resource improvement. The conservative B/C/D quality success count is {local_counts['repair_success']}. Local success is not run-level superiority; denominators include cached proposals under the common budget policy.", '',
             '| Failure class / operator | Repairs | Quality successes | Witness elimination fraction |', '|---|---:|---:|---:|']
    for r in repairs:
        elim = 'unresolved' if r['elimination_rate'] is None else f"{r['elimination_rate']:.3f}"
        rows.append(f"| {r['failure_class']} / {r['operator']} | {r['repairs']} | {r['successes']} | {elim} |")
    rows += ['', 'Representative serialized parent/child circuits, witnesses, provenance and comparisons are in `results/v0.2/examples/`. They can be replayed with `ftqec verify`.','']
    for row in example_rows:
        rows.append(f"- `{row['label']}` from `{row['source_run']}`: {row['provenance']['repair_operator']}, parent lower bound {row['parent_bounds']['lower_bound']} -> child {row['child_bounds']['lower_bound']}; source-witness elimination={row['outcome']['eliminates_source_witness']}, quality success={row['outcome']['repair_success']}.")
    rows += ['', 'The absence of overall improvement has several concrete explanations. Non-CSS product readout supplies vulnerable terminal records outside this extraction-repair library. The four-qubit CSS example has limited attainable quality, while the successful Steane seed already starts at the target. Moreover, repairs that eliminate one witness without improving the certified distance/resources can be dominated and removed from the finite beam, preventing accumulation of neutral intermediate repairs across checks. These observations motivate future readout synthesis, multi-witness constraint retention and larger predeclared pilots; they do not justify retuning or claiming this pilot positive.', '',
             '## Decoder-dependent failures', '',
             'Every candidate also trains/evaluates the deterministic detector-to-logical recovery baseline through weight one. Raw `decoder` records preserve coverage, resolved cases, failures and example nonzero-syndrome collisions. These counts are separate from circuit distance and are not LER estimates. Tie choices can cause decoder failure even with nonzero detectors; a dedicated regression demonstrates the distinction.', '',
             '## Performance and verification', '',
             'Three repeated-round Steane circuits were profiled using both the original forward single-fault path and the new suffix-map path, each three times, with exact signature equality. Median speedups:', '']
    for r in performance:
        rows.append(f"- `{r['architecture_id']}`: {r['fault_variants']} elementary variants, {r['operations']} IR operations; {r['median_speedup']:.2f}x; forward median {statistics.median(r['forward_seconds']):.6f}s -> suffix median {statistics.median(r['suffix_seconds']):.6f}s.")
    rows += ['', 'The final profile now spreads cost over signature enumeration, JSON/dataclass serialization, IR validation and search bookkeeping. Packed suffix maps remove the demonstrated repeated-propagation bottleneck. High-weight scaling and larger-code throughput remain unmeasured; no held-out execution is used to support a performance claim.', '',
             f"Full suite: {verification['passed']} passed, {verification['failures']} failures, {verification['skipped']} skips. All {len(runs)} raw runs validate against the native V0.2 schema, and all {replayed} reported witness instances replay independently from rebuilt serialized circuits. Dense-state tests cover repeated CSS/non-CSS semantics, actual measurement/reset outcomes, flags, preparation-output noise and both logical memory bases. Full editable installation and CLI paths are tested without manually setting PYTHONPATH.", '',
             '## Held-out readiness gate', '',
             '- Correctness: passing tests, independent temporal semantics checks, independently verified witnesses under the explicitly limited model.',
             '- Search: no observed strongest-distance or target-reach advantage; not statistically established. Three seeds are a pilot, not broad evidence.',
             '- Performance: practical small-development-code evaluation throughput; held-out-size scaling untested.',
             '- Isolation: no held-out code was run, no final architecture packages imported, and no external optimal-architecture search performed. The held-out directory contains only its original README.', '',
             '**NOT_READY_FOR_HELD_OUT.** Preserve the frozen research targets. The next development work should address final readout and accumulation of useful witness-eliminating intermediate candidates, then test a new, predeclared multi-seed protocol.']
    (root/'docs/V0_2_RESULTS.md').write_text('\n'.join(rows)+'\n')
    print(json.dumps({'gate':gate['status'],'runs_validated':len(runs),'witnesses_replayed':replayed,
                      'local_repair_counts':dict(local_counts)},indent=2))


if __name__=='__main__': main()
