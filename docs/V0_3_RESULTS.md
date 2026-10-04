# V0.3 malignant-gradient research results

**RESULT B — Partial local success; no validated general advantage. NOT_READY_FOR_HELD_OUT.**

The prospective criteria in `V0_3_HYPOTHESIS.md` were committed before the final experiment. No post-result algorithm tuning was performed. Baseline v0.2.0 and its raw results remain intact.

## Model and matched protocol

css4, noncss4, perfect5, Steane; X/Z memory, three extraction rounds, ideal encoded input, noisy gates/ancilla resets/readouts and physical product terminal readout. One optional additional noisy terminal round is available to every strategy. Six seeds 0–5, six shared initial candidates, 32 slots, 26 mutation slots, 200000 certification and spectrum work entries. Ten variants, 480 runs, 15360 slots. Unknown/capped counts never guide as zeros. Exact lower bounds are independent of the heuristic.

## All codes, seeds and strategies

| Code | Basis | Variant | d_c lower bounds, seeds 0–5 | Targets / 6 | Evaluations to target | Compositions | Mean seconds |
|---|---|---|---|---|---|---|---|
| css4 | X | mixed | [2, 2, 2, 2, 2, 2] | 0 | [None, None, None, None, None, None] | 0 | 1.689 |
| css4 | X | random | [2, 2, 2, 2, 2, 2] | 0 | [None, None, None, None, None, None] | 0 | 0.948 |
| css4 | X | resource | [2, 2, 2, 2, 2, 2] | 0 | [None, None, None, None, None, None] | 0 | 0.462 |
| css4 | X | v02 | [2, 2, 2, 2, 2, 2] | 0 | [None, None, None, None, None, None] | 0 | 1.136 |
| css4 | X | v03 | [2, 2, 2, 2, 2, 2] | 0 | [None, None, None, None, None, None] | 0 | 1.768 |
| css4 | X | v03_arbitrary | [2, 2, 2, 2, 2, 2] | 0 | [None, None, None, None, None, None] | 1 | 1.559 |
| css4 | X | v03_no_coverage | [2, 2, 2, 2, 2, 2] | 0 | [None, None, None, None, None, None] | 0 | 1.704 |
| css4 | X | v03_no_protection | [2, 2, 2, 2, 2, 2] | 0 | [None, None, None, None, None, None] | 0 | 1.738 |
| css4 | X | v03_raw | [2, 2, 2, 2, 2, 2] | 0 | [None, None, None, None, None, None] | 0 | 1.692 |
| css4 | X | v03_signature | [2, 2, 2, 2, 2, 2] | 0 | [None, None, None, None, None, None] | 0 | 1.642 |
| css4 | Z | mixed | [2, 2, 2, 2, 2, 2] | 0 | [None, None, None, None, None, None] | 0 | 1.458 |
| css4 | Z | random | [2, 2, 2, 2, 2, 2] | 0 | [None, None, None, None, None, None] | 0 | 0.802 |
| css4 | Z | resource | [2, 2, 2, 2, 2, 2] | 0 | [None, None, None, None, None, None] | 0 | 0.420 |
| css4 | Z | v02 | [2, 2, 2, 2, 2, 2] | 0 | [None, None, None, None, None, None] | 0 | 1.210 |
| css4 | Z | v03 | [2, 2, 2, 2, 2, 2] | 0 | [None, None, None, None, None, None] | 6 | 1.478 |
| css4 | Z | v03_arbitrary | [2, 2, 2, 2, 2, 2] | 0 | [None, None, None, None, None, None] | 7 | 1.474 |
| css4 | Z | v03_no_coverage | [2, 2, 2, 2, 2, 2] | 0 | [None, None, None, None, None, None] | 0 | 1.868 |
| css4 | Z | v03_no_protection | [2, 2, 2, 2, 2, 2] | 0 | [None, None, None, None, None, None] | 1 | 1.528 |
| css4 | Z | v03_raw | [2, 2, 2, 2, 2, 2] | 0 | [None, None, None, None, None, None] | 0 | 1.578 |
| css4 | Z | v03_signature | [2, 2, 2, 2, 2, 2] | 0 | [None, None, None, None, None, None] | 0 | 1.615 |
| noncss4 | X | mixed | [1, 1, 1, 1, 1, 1] | 0 | [None, None, None, None, None, None] | 0 | 0.689 |
| noncss4 | X | random | [1, 1, 1, 1, 1, 1] | 0 | [None, None, None, None, None, None] | 0 | 0.497 |
| noncss4 | X | resource | [1, 1, 1, 1, 1, 1] | 0 | [None, None, None, None, None, None] | 0 | 0.221 |
| noncss4 | X | v02 | [1, 1, 1, 1, 1, 1] | 0 | [None, None, None, None, None, None] | 0 | 0.531 |
| noncss4 | X | v03 | [1, 1, 1, 1, 1, 1] | 0 | [None, None, None, None, None, None] | 0 | 0.701 |
| noncss4 | X | v03_arbitrary | [1, 1, 1, 1, 1, 1] | 0 | [None, None, None, None, None, None] | 0 | 0.738 |
| noncss4 | X | v03_no_coverage | [1, 1, 1, 1, 1, 1] | 0 | [None, None, None, None, None, None] | 0 | 0.792 |
| noncss4 | X | v03_no_protection | [1, 1, 1, 1, 1, 1] | 0 | [None, None, None, None, None, None] | 0 | 0.688 |
| noncss4 | X | v03_raw | [1, 1, 1, 1, 1, 1] | 0 | [None, None, None, None, None, None] | 0 | 0.749 |
| noncss4 | X | v03_signature | [1, 1, 1, 1, 1, 1] | 0 | [None, None, None, None, None, None] | 0 | 0.608 |
| noncss4 | Z | mixed | [1, 1, 1, 1, 1, 1] | 0 | [None, None, None, None, None, None] | 0 | 0.643 |
| noncss4 | Z | random | [1, 1, 1, 1, 1, 1] | 0 | [None, None, None, None, None, None] | 0 | 0.463 |
| noncss4 | Z | resource | [1, 1, 1, 1, 1, 1] | 0 | [None, None, None, None, None, None] | 0 | 0.232 |
| noncss4 | Z | v02 | [1, 1, 1, 1, 1, 1] | 0 | [None, None, None, None, None, None] | 0 | 0.525 |
| noncss4 | Z | v03 | [1, 1, 1, 1, 1, 1] | 0 | [None, None, None, None, None, None] | 0 | 0.673 |
| noncss4 | Z | v03_arbitrary | [1, 1, 1, 1, 1, 1] | 0 | [None, None, None, None, None, None] | 0 | 0.642 |
| noncss4 | Z | v03_no_coverage | [1, 1, 1, 1, 1, 1] | 0 | [None, None, None, None, None, None] | 0 | 0.772 |
| noncss4 | Z | v03_no_protection | [1, 1, 1, 1, 1, 1] | 0 | [None, None, None, None, None, None] | 0 | 0.652 |
| noncss4 | Z | v03_raw | [1, 1, 1, 1, 1, 1] | 0 | [None, None, None, None, None, None] | 0 | 0.690 |
| noncss4 | Z | v03_signature | [1, 1, 1, 1, 1, 1] | 0 | [None, None, None, None, None, None] | 0 | 0.567 |
| perfect5 | X | mixed | [1, 1, 1, 1, 1, 1] | 0 | [None, None, None, None, None, None] | 0 | 1.429 |
| perfect5 | X | random | [1, 1, 1, 1, 1, 1] | 0 | [None, None, None, None, None, None] | 0 | 0.994 |
| perfect5 | X | resource | [1, 1, 1, 1, 1, 1] | 0 | [None, None, None, None, None, None] | 0 | 0.582 |
| perfect5 | X | v02 | [1, 1, 1, 1, 1, 1] | 0 | [None, None, None, None, None, None] | 0 | 1.086 |
| perfect5 | X | v03 | [1, 1, 1, 1, 1, 1] | 0 | [None, None, None, None, None, None] | 0 | 1.391 |
| perfect5 | X | v03_arbitrary | [1, 1, 1, 1, 1, 1] | 0 | [None, None, None, None, None, None] | 0 | 1.313 |
| perfect5 | X | v03_no_coverage | [1, 1, 1, 1, 1, 1] | 0 | [None, None, None, None, None, None] | 0 | 1.529 |
| perfect5 | X | v03_no_protection | [1, 1, 1, 1, 1, 1] | 0 | [None, None, None, None, None, None] | 0 | 1.431 |
| perfect5 | X | v03_raw | [1, 1, 1, 1, 1, 1] | 0 | [None, None, None, None, None, None] | 0 | 1.384 |
| perfect5 | X | v03_signature | [1, 1, 1, 1, 1, 1] | 0 | [None, None, None, None, None, None] | 0 | 1.206 |
| perfect5 | Z | mixed | [1, 1, 1, 1, 1, 1] | 0 | [None, None, None, None, None, None] | 0 | 1.168 |
| perfect5 | Z | random | [1, 1, 1, 1, 1, 1] | 0 | [None, None, None, None, None, None] | 0 | 1.024 |
| perfect5 | Z | resource | [1, 1, 1, 1, 1, 1] | 0 | [None, None, None, None, None, None] | 0 | 0.596 |
| perfect5 | Z | v02 | [1, 1, 1, 1, 1, 1] | 0 | [None, None, None, None, None, None] | 0 | 1.078 |
| perfect5 | Z | v03 | [1, 1, 1, 1, 1, 1] | 0 | [None, None, None, None, None, None] | 0 | 1.166 |
| perfect5 | Z | v03_arbitrary | [1, 1, 1, 1, 1, 1] | 0 | [None, None, None, None, None, None] | 0 | 1.210 |
| perfect5 | Z | v03_no_coverage | [1, 1, 1, 1, 1, 1] | 0 | [None, None, None, None, None, None] | 0 | 1.376 |
| perfect5 | Z | v03_no_protection | [1, 1, 1, 1, 1, 1] | 0 | [None, None, None, None, None, None] | 0 | 1.207 |
| perfect5 | Z | v03_raw | [1, 1, 1, 1, 1, 1] | 0 | [None, None, None, None, None, None] | 0 | 1.307 |
| perfect5 | Z | v03_signature | [1, 1, 1, 1, 1, 1] | 0 | [None, None, None, None, None, None] | 0 | 1.189 |
| steane | X | mixed | [2, 3, 3, 2, 3, 2] | 3 | [None, 29, 24, None, 4, None] | 1 | 3.580 |
| steane | X | random | [2, 2, 2, 2, 3, 2] | 1 | [None, None, None, None, 4, None] | 0 | 2.559 |
| steane | X | resource | [2, 2, 2, 2, 3, 2] | 1 | [None, None, None, None, 4, None] | 0 | 1.528 |
| steane | X | v02 | [2, 2, 2, 2, 3, 2] | 1 | [None, None, None, None, 4, None] | 0 | 2.530 |
| steane | X | v03 | [2, 3, 2, 2, 3, 2] | 2 | [None, 11, None, None, 4, None] | 1 | 4.154 |
| steane | X | v03_arbitrary | [2, 2, 3, 2, 3, 2] | 2 | [None, None, 28, None, 4, None] | 1 | 3.431 |
| steane | X | v03_no_coverage | [2, 3, 3, 3, 3, 2] | 4 | [None, 7, 22, 9, 4, None] | 3 | 3.967 |
| steane | X | v03_no_protection | [2, 3, 2, 2, 3, 2] | 2 | [None, 11, None, None, 4, None] | 0 | 4.555 |
| steane | X | v03_raw | [2, 3, 2, 2, 3, 2] | 2 | [None, 11, None, None, 4, None] | 1 | 4.395 |
| steane | X | v03_signature | [2, 2, 2, 2, 3, 2] | 1 | [None, None, None, None, 4, None] | 0 | 3.556 |
| steane | Z | mixed | [3, 3, 3, 3, 2, 3] | 5 | [6, 21, 18, 4, None, 8] | 2 | 5.019 |
| steane | Z | random | [3, 2, 2, 3, 2, 2] | 2 | [6, None, None, 4, None, None] | 0 | 2.584 |
| steane | Z | resource | [3, 2, 2, 3, 2, 2] | 2 | [6, None, None, 4, None, None] | 0 | 1.761 |
| steane | Z | v02 | [3, 2, 2, 3, 2, 2] | 2 | [6, None, None, 4, None, None] | 0 | 3.045 |
| steane | Z | v03 | [3, 3, 2, 3, 3, 2] | 4 | [6, 21, None, 4, 13, None] | 3 | 4.218 |
| steane | Z | v03_arbitrary | [3, 3, 3, 3, 3, 2] | 5 | [6, 20, 25, 4, 19, None] | 5 | 4.062 |
| steane | Z | v03_no_coverage | [3, 3, 3, 3, 3, 3] | 6 | [6, 7, 8, 4, 7, 9] | 22 | 8.733 |
| steane | Z | v03_no_protection | [3, 2, 2, 3, 3, 2] | 3 | [6, None, None, 4, 22, None] | 0 | 4.241 |
| steane | Z | v03_raw | [3, 2, 2, 3, 2, 2] | 2 | [6, None, None, 4, None, None] | 1 | 3.756 |
| steane | Z | v03_signature | [3, 2, 2, 3, 2, 2] | 2 | [6, None, None, 4, None, None] | 0 | 3.958 |

## Frozen primary tests

Positive margins favor V0.3. QD is measured at the common attained tier >=2; unequal-quality failures are not hidden in that conditional metric. Unreached target gets 33 evaluations. Exact paired sign tests use non-ties, with Holm correction over all 12 endpoints. These are small development experiments; shared code/seed dependence limits generalization. Passing also requires favorable cases across two codes and three seeds.

| Baseline | Endpoint | W/T/L | Mean margin | Holm p | Frozen pass |
|---|---|---|---|---|---|
| random | target_success | 3/45/0 | 0.0625 | 1 | False |
| random | target_evaluations | 3/45/0 | 1.125 | 1 | False |
| random | distance | 3/45/0 | 0.0625 | 1 | False |
| random | matched_QD | 4/13/7 | -20.125 | 1 | False |
| resource | target_success | 3/45/0 | 0.0625 | 1 | False |
| resource | target_evaluations | 3/45/0 | 1.125 | 1 | False |
| resource | distance | 3/45/0 | 0.0625 | 1 | False |
| resource | matched_QD | 4/9/11 | -92.33333333333333 | 1 | False |
| v02 | target_success | 3/45/0 | 0.0625 | 1 | False |
| v02 | target_evaluations | 3/45/0 | 1.125 | 1 | False |
| v02 | distance | 3/45/0 | 0.0625 | 1 | False |
| v02 | matched_QD | 2/18/4 | -26.458333333333332 | 1 | False |

## Direct gradient and ancestry

Probabilities below use equal-distance parent-child edges and descendants observed within the remaining budget. They are censored, endogenous search trajectories, not causal probabilities or independent trials. Observation exposure and reduction-size correlation are saved in `results/v0.3/gradient.json`.

| Variant | Count reduced: future gains / edges | Count not reduced: future gains / edges | Reduction-size correlation |
|---|---|---|---|
| random | 0/374 | 4/828 | None |
| resource | 0/103 | 0/1102 | None |
| v02 | 0/625 | 10/563 | None |
| v03 | 10/267 | 7/944 | -0.09274925128700502 |
| mixed | 5/233 | 13/966 | -0.05137628415923142 |
| v03_raw | 3/281 | 7/929 | -0.03708369667408172 |
| v03_signature | 0/467 | 6/697 | None |
| v03_no_protection | 1/274 | 10/902 | -0.03432594929715777 |
| v03_arbitrary | 21/297 | 8/914 | 0.027008066017057998 |
| v03_no_coverage | 19/362 | 2/761 | 0.10951317236700778 |
| all_v03_edges | 10/284 | 7/944 | -0.08975880725388348 |

V0.3 has 17 parent-child distance-gain events; 10 have a multi-guided-repair ancestry containing neutral class progress. These events are not necessarily independent architectures or improvements beyond the shared initial best. Every gain ancestry and intermediate spectrum is saved in `repair_chains.json`. The strict contiguous-guided definition yields 9/17; three exceed the best shared initial distance. The table composition column is the broader ancestry metric.

Example css4 Z seed 1: nodes [1, 9, 15, 18]; operators ['initial_population', 'reverse_implicated_order', 'split_prefix_flag', 'independent_full_interval_flag']; neutral progress steps 1; added resources {'Q': 2, 'D': 24, 'QD': 266, 'two_q_gates': 12}.

Example css4 Z seed 1: nodes [1, 9, 15, 19, 22]; operators ['initial_population', 'reverse_implicated_order', 'split_prefix_flag', 'split_suffix_flag', 'independent_full_interval_flag']; neutral progress steps 2; added resources {'Q': 3, 'D': 36, 'QD': 435, 'two_q_gates': 18}.

## Repair-level evidence and resource costs

Mechanism-key disappearance, net count reduction, exact source removal and elimination of every transportable raw realization of a source class are separate measures. Unknown/ambiguous transport receives no class-elimination credit. Full operator/failure tables and QD-per-class costs are saved in `operator_statistics.json`.
An audit refined 177 raw whole-class diagnostic labels to unresolved because the parent enumeration was capped. Raw files are preserved. This reporting correction changes no selection, operator history, spectrum, certificate or frozen endpoint.

| V0.3 operator | Failure class | Net class successes / attempts | Mean added QD | QD / eliminated class |
|---|---|---|---|---|
| independent_full_interval_flag | SAME_CHECK_HOOK | 25/25 | 161.84 | 38.217110296678754 |
| independent_full_interval_flag | CROSS_CHECK_COLLISION | 1/1 | 181.00 | 2.3205128205128207 |
| split_temporal_flag_records | FINAL_READOUT | 1/1 | 96.00 | 1.263157894736842 |
| split_suffix_flag | CROSS_CHECK_COLLISION | 3/4 | 130.25 | 3.406216109632259 |
| split_suffix_flag | SAME_CHECK_HOOK | 30/42 | 142.81 | 67.0114475500345 |
| split_suffix_flag | FINAL_READOUT | 2/3 | 137.00 | 5.544871794871796 |
| split_prefix_flag | FLAG_CANCELLATION | 3/5 | 195.40 | 2.136441038739889 |
| independent_full_interval_flag | INTERACTION_ORDER_HOOK | 22/39 | 202.90 | 10.670003223889776 |
| split_temporal_flag_records | SAME_CHECK_HOOK | 2/4 | 160.50 | 3.467741935483871 |
| split_prefix_flag | FINAL_READOUT | 1/2 | 110.50 | 0.6130952380952381 |
| split_prefix_flag | SAME_CHECK_HOOK | 18/37 | 147.14 | 87.8745491971548 |
| split_suffix_flag | INTERACTION_ORDER_HOOK | 11/23 | 187.61 | 8.69255280935084 |
| split_prefix_flag | INTERACTION_ORDER_HOOK | 11/24 | 200.04 | 16.37292277614858 |
| split_suffix_flag | OTHER | 19/45 | 163.73 | 62.58991228070175 |
| split_temporal_flag_records | INTERACTION_ORDER_HOOK | 7/18 | 260.94 | 23.8269701019701 |
| independent_full_interval_flag | OTHER | 10/27 | 154.30 | 66.75357142857143 |
| change_implicated_check_order | CROSS_CHECK_COLLISION | 4/12 | 29.00 | 121.8 |
| separate_hook_support | INTERACTION_ORDER_HOOK | 16/50 | 3.06 | 0.0 |
| separate_hook_support | SAME_CHECK_HOOK | 44/157 | 2.27 | 1.8068181818181819 |
| split_prefix_flag | OTHER | 4/20 | 150.15 | 70.20930232558139 |
| reverse_implicated_order | SAME_CHECK_HOOK | 24/157 | 3.88 | 6.5 |
| reverse_implicated_order | INTERACTION_ORDER_HOOK | 6/78 | 1.46 | 0.25 |
| split_temporal_flag_records | OTHER | 1/14 | 162.64 | 91.0 |
| reverse_implicated_order | OTHER | 13/270 | 8.83 | -1.6153846153846154 |
| reverse_implicated_order | CROSS_CHECK_COLLISION | 1/34 | 7.06 | -0.75 |
| separate_syndrome_ancillas | CROSS_CHECK_COLLISION | 0/59 | 968.39 | None |
| serialize_cross_check_gadgets | CROSS_CHECK_COLLISION | 0/29 | 1489.86 | None |
| reverse_implicated_order | FINAL_READOUT | 0/18 | 6.33 | None |
| redirect_hook_order | INTERACTION_ORDER_HOOK | 0/3 | 0.00 | None |
| noisy_terminal_verification_round | BOUNDARY_READOUT_FAILURE | 0/2 | 136.00 | None |
| split_temporal_flag_records | CROSS_CHECK_COLLISION | 0/2 | 158.00 | None |
| independent_full_interval_flag | CROSS_CHECK_OVERLAP | 0/1 | 247.00 | None |

## Ablations, runtime and limits

Raw, signature, structural, no-protection, arbitrary-order and no-coverage comparisons are all in the complete table above. No best definition is declared from local count reduction alone. Signature equivalence can collapse all malignant mechanisms to a single logical-effect class. All spectrum trajectories, beam survival/pruning reasons, ancestry and mutation coverage estimates are retained losslessly in compressed raw JSON. Exact circuit/signature/class caches serve duplicates; tiny mutations are reevaluated fully rather than assuming invalid local reuse.

Total wall time 998.231s; summed search time 834.839s; 15.387 slots/s including output. Separate function profiling is saved. Validation replayed 1058039 unique witnesses (2368557 reported instances) and audited all 3507 distinct nontrivial certified bounds, including 87 distinct distance-gain exclusions. Tests: 96 passed, zero skips. Held-out runs: zero.

## Explicit answers to the 20 research questions

1. Useful gradient: neutral count-reduction edges yielded 10/267 later distance gains, versus 7/944 nonreducing edges. This is descriptive and does not establish general predictive utility.
2. Source versus whole class: V0.3 source eliminations 388/1206; transported whole-class eliminated/surviving/unresolved counts 363/824/19. Net new alternatives are separately counted.
3. Composition before increase: 9/17 gain events have consecutive guided neutral class reductions followed by a guided gain; 3 also exceed the best shared initial distance. This demonstrates composition, not necessity.
4. Progress protection: strongest-distance V0.3 versus no-protection W/T/L {'wins': 1, 'ties': 47, 'losses': 0}; resource and target outcomes are in the complete matched table.
5. Best equivalence: structural versus raw W/T/L {'wins': 2, 'ties': 46, 'losses': 0}; structural versus signature {'wins': 3, 'ties': 45, 'losses': 0}. No universal best is established by tied or code-dependent results.
6. Highest observed class-level operator fractions: [('independent_full_interval_flag', 'SAME_CHECK_HOOK', 25, 25), ('independent_full_interval_flag', 'CROSS_CHECK_COLLISION', 1, 1), ('split_temporal_flag_records', 'FINAL_READOUT', 1, 1)]. Small denominators are not reliable universal rankings.
7. Coverage prioritization: V0.3 versus no-coverage distance W/T/L {'wins': 0, 'ties': 44, 'losses': 4}; prospective coverage is estimated, not certified elimination.
8. Boundary bottleneck: 4776 distinct architectures contain an observed unsupported terminal class; minimum-witness family instances {'EXTRACTION_FAILURE': 15199} across all variants. This counts mechanisms, not stochastic failure probabilities.
9. Against random: distance W/T/L 3/45/0; frozen endpoint pass False.
10. Against resource search: distance W/T/L 3/45/0; frozen endpoint pass False.
11. Against V0.2 CEGIS: distance W/T/L 3/45/0; frozen endpoint pass False.
12. Quantitative margins: all 12 paired endpoints, conditional QD units, target evaluation differences and adjusted p-values are reported above and in paired_comparisons.json.
13. Cross-code/seed persistence: frozen endpoint success requires two favorable codes and three favorable seeds; full criteria passed=False. Favorable codes/seeds are listed for each endpoint in paired_comparisons.json.
14. Ablation: arbitrary-order W/T/L {'wins': 1, 'ties': 45, 'losses': 2}; equivalence, protection and coverage margins above. No post-hoc tuning followed these results.
15. Resource costs: per-operator added Q/D/QD/two-qubit gates, QD per class removed and every per-edge QD per distance tier are in raw records and operator_statistics.json. The resource frontier retains tradeoffs rather than allowing unlimited redundant rounds.
16. Multi-step gains: 9/17 strict events, with overlapping ancestries. The broad ancestry metric was 10/17; it includes one noncontiguous case. Neither count proves that a shorter repair was impossible.
17. Unsupported mechanisms: destructive product-readout/basis-only failures and arbitrary incompatible non-CSS boundary readout. One noisy repeated extraction round is available for mixed boundary faults; it provides no ideal protection.
18. Core hypothesis: RESULT B — Partial local success; no validated general advantage. Passing local spectrum tests or eliminating a source witness does not establish synthesis superiority.
19. Algorithm freeze: no; all readiness conditions are not met. ALGORITHM_FREEZE.md is not created.
20. NOT_READY_FOR_HELD_OUT. Reasons: V0.3 does not beat every required baseline under the frozen multiplicity-corrected, cross-code/cross-seed criteria. Practical throughput at held-out code size has not been established; only development codes were run. Pure product-readout boundary failures remain unsupported.

## Local evidence does not satisfy the frozen general criterion

The requested RESULT B interpretation fits the restricted evidence: targets 6/48 versus 3/48 for each primary baseline, three distance wins all on Steane and seeds 1/4, nine strict composition events, and three strict chains beyond the shared initial best. No endpoint passes the unchanged frozen tests: every Holm-adjusted p-value is 1.0. The +6.25 percentage-point target margin and +0.0625 mean distance margin are descriptive. No new success threshold is introduced, and the algorithm is not ready to freeze.

Class-reducing nodes were expanded more often. Among equal-distance edges with at least one observed descendant: [{'reduced': True, 'expanded_edges': 208, 'future_gains': 10, 'fraction': 0.04807692307692308}, {'reduced': False, 'expanded_edges': 166, 'future_gains': 7, 'fraction': 0.04216867469879518}]. This exposure restriction still does not remove adaptive selection, ancestry dependence or censoring. Larger reductions did not show a positive size/gain correlation (r=-0.093).

Disabling coverage prioritization reached 10/48 targets versus 6/48 for the frozen default. This is an exploratory ablation, not a promoted replacement algorithm or a retrospective readiness pass. Matched-tier mean QD was higher for V0.3 by 20.125 versus random, 92.333 versus resource and 26.458 versus V0.2 CEGIS.

Strict global-distance-gain example steane-X-seed1-v03.json.gz: d_c 2 -> 3; architecture sequence ['5e75e0c5b4ffcc9e40cc', '106d0cc99243bb503309', 'c739d88f4d1945db7ab0']; M_2=[33, 32, 0]; operators ['change_implicated_check_order', 'independent_full_interval_flag']; resource delta {'Q': 1, 'D': 39, 'QD': 893, 'two_q_gates': 6}. Targeted classes and all nodes are in strict_composition_analysis.json.

Strict global-distance-gain example steane-Z-seed1-v03.json.gz: d_c 2 -> 3; architecture sequence ['4071de20127569943955', '02a2f0e69bdfa8cd9517', '23620508efe3c627483f']; M_2=[53, 30, 0]; operators ['independent_full_interval_flag', 'independent_full_interval_flag']; resource delta {'Q': 0, 'D': 24, 'QD': 240, 'two_q_gates': 12}. Targeted classes and all nodes are in strict_composition_analysis.json.

Strict global-distance-gain example steane-Z-seed4-v03.json.gz: d_c 2 -> 3; architecture sequence ['98db4e237fbb33809fe7', '0dbbe6b08721feea8673', '0ea676cb53bbe8b56459']; M_2=[37, 27, 0]; operators ['reverse_implicated_order', 'independent_full_interval_flag']; resource delta {'Q': 1, 'D': 12, 'QD': 397, 'two_q_gates': 6}. Targeted classes and all nodes are in strict_composition_analysis.json.
