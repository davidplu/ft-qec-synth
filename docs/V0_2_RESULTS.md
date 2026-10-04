# V0.2 research results

**NOT_READY_FOR_HELD_OUT.** The repeated-memory implementation and independent checks pass, but this pilot does not support the claim that CEGIS reaches stronger architectures more efficiently than unguided search.

## Baseline and exact changes

V0.1 delivered source was not a Git repository. It was preserved as baseline commit `0291500da4c5977a093988f918c8baf8ffdf867e`; development uses branch `development/v0.2`. Packaging/serialization fixes were committed separately, with 34 passing baseline tests and zero skips. The original algebra, gadgets, candidates, scheduler and search were extended rather than replaced.

V0.2 adds repeated rounds, temporal detectors and phase-correct compatible-stabilizer-subgroup readout closure; destructive X/Z logical memory readout; separate bounded minimum-weight decoder metrics; round/check/location metadata; backward packed transfer maps; independently replayed witnesses; structural analysis and generic repairs; mutation provenance; matched ablations; JSON-native public objects and mandatory complete dev dependencies. V0.1 ideal-boundary mode remains explicitly selectable.

## Frozen protocol

Development inputs: css4, noncss4, perfect5 and Steane. Both X/Z memory at logical index 0; R=3; ideal encoded input; noisy ancilla resets, gates and readouts; physical terminal product readout; implicit idles and optional input noise disabled in this pilot. Maximum physical fault weight 3; 200000 work entries per search; target d_c >= 3.

Seeds [0, 1, 2]; four strategies; six identical initial candidates; 24 slots and 18 mutation proposals per run. Duplicates consume slots with a common cache policy. 96 runs, 2304 slots, 30.676 summed wall seconds. Time is measured, not equalized. Exact model and limitations are in `FAULT_MODEL.md` and `V0_2_LIMITATIONS.md`.

## Multi-seed distance comparison

Each entry lists the best certified d_c lower bound at seeds 0, 1 and 2. Values are lower bounds, not assertions of exact distance.

| Code | Memory | Random | Resource | CEGIS | Mixed |
|---|---|---|---|---|---|
| css4 | X | [2, 2, 2] | [2, 2, 2] | [2, 2, 2] | [2, 2, 2] |
| css4 | Z | [2, 2, 2] | [2, 2, 2] | [2, 2, 2] | [2, 2, 2] |
| noncss4 | X | [1, 1, 1] | [1, 1, 1] | [1, 1, 1] | [1, 1, 1] |
| noncss4 | Z | [1, 1, 1] | [1, 1, 1] | [1, 1, 1] | [1, 1, 1] |
| perfect5 | X | [1, 1, 1] | [1, 1, 1] | [1, 1, 1] | [1, 1, 1] |
| perfect5 | Z | [1, 1, 1] | [1, 1, 1] | [1, 1, 1] | [1, 1, 1] |
| steane | X | [2, 2, 2] | [2, 2, 2] | [2, 2, 2] | [2, 2, 2] |
| steane | Z | [3, 2, 2] | [3, 2, 2] | [3, 2, 2] | [3, 2, 2] |

CEGIS versus random: 0 stronger-distance wins, 24 ties and 0 losses across the 24 paired code/basis/seed conditions. No strongest-distance improvement was observed. These cohorts share code structure and must not be pooled as independent statistical trials.

## Target efficiency, ablations and resource frontiers

| Strategy | Runs reaching target | Fraction | Mean seconds/run |
|---|---:|---:|---:|
| random | 1/24 | 0.042 | 0.321 |
| resource | 1/24 | 0.042 | 0.235 |
| cegis | 1/24 | 0.042 | 0.400 |
| mixed | 1/24 | 0.042 | 0.322 |

All target successes occurred in the common initial population: True. Accordingly, evaluations-to-target are not evidence of a guided-mutation benefit. Unreached targets remain in the reach-fraction denominator; target-conditioned timing/resource statistics remain explicitly conditional. Full per-seed first-tier evaluation/time and best Q/D/QD/2Q metrics are saved in every raw run and `aggregate.json`.

Target-conditioned frontiers compare Q, D, QD and two-qubit gates separately after requiring the certified distance threshold. Most frontiers are empty, which is an experimental result rather than a missing export. Representative nonempty vectors:

- `steane-Z-seed0-cegis.json`, `d2aae03a1a3c2a98e76b`: Q=13, D=163, QD=2119, 2Q=126, bound=LOWER_BOUND >= 3.
- `steane-Z-seed0-cegis.json`, `6bb325edc388547b9652`: Q=21, D=142, QD=2982, 2Q=126, bound=LOWER_BOUND >= 3.
- `steane-Z-seed0-mixed.json`, `93426eb5417dcb752172`: Q=13, D=184, QD=2392, 2Q=126, bound=LOWER_BOUND >= 3.
- `steane-Z-seed0-random.json`, `b7c70e55b7d93483daaf`: Q=21, D=139, QD=2919, 2Q=126, bound=LOWER_BOUND >= 3.
- `steane-Z-seed0-random.json`, `ad7604f861278966c3d2`: Q=13, D=169, QD=2197, 2Q=126, bound=LOWER_BOUND >= 3.
- `steane-Z-seed0-resource.json`, `93426eb5417dcb752172`: Q=13, D=184, QD=2392, 2Q=126, bound=LOWER_BOUND >= 3.
- `steane-Z-seed0-resource.json`, `3ea9952d49c8bfd59a56`: Q=10, D=253, QD=2530, 2Q=126, bound=EXACT >= 3.

## Repairs and counterexamples

544 guided repair proposals were evaluated. 242/544 transportable source witnesses were eliminated. 17 proposals improved their parent's certified lower bound, and 13 preserved exact distance with resource improvement. The conservative B/C/D quality success count is 30. Local success is not run-level superiority; denominators include cached proposals under the common budget policy.

| Failure class / operator | Repairs | Quality successes | Witness elimination fraction |
|---|---:|---:|---:|
| CROSS_CHECK_COLLISION / change_implicated_check_order | 1 | 0 | 0.000 |
| CROSS_CHECK_COLLISION / separate_syndrome_ancillas | 1 | 0 | 0.000 |
| FLAG_CANCELLATION / independent_full_interval_flag | 12 | 0 | 1.000 |
| FLAG_CANCELLATION / split_prefix_flag | 5 | 0 | 1.000 |
| FLAG_CANCELLATION / split_suffix_flag | 1 | 0 | 0.000 |
| INTERACTION_ORDER_HOOK / independent_full_interval_flag | 45 | 0 | 0.578 |
| INTERACTION_ORDER_HOOK / redirect_hook_order | 7 | 3 | 0.000 |
| INTERACTION_ORDER_HOOK / reverse_implicated_order | 19 | 1 | 0.579 |
| INTERACTION_ORDER_HOOK / separate_hook_support | 8 | 0 | 0.625 |
| INTERACTION_ORDER_HOOK / split_prefix_flag | 35 | 0 | 0.571 |
| INTERACTION_ORDER_HOOK / split_suffix_flag | 27 | 0 | 0.037 |
| INTERACTION_ORDER_HOOK / split_temporal_flag_records | 5 | 0 | 0.600 |
| OTHER / independent_full_interval_flag | 52 | 0 | 0.000 |
| OTHER / reverse_implicated_order | 29 | 4 | 0.000 |
| OTHER / split_prefix_flag | 44 | 0 | 0.000 |
| OTHER / split_suffix_flag | 35 | 0 | 0.000 |
| OTHER / split_temporal_flag_records | 7 | 0 | 0.000 |
| SAME_CHECK_HOOK / independent_full_interval_flag | 64 | 15 | 1.000 |
| SAME_CHECK_HOOK / reverse_implicated_order | 31 | 3 | 1.000 |
| SAME_CHECK_HOOK / separate_hook_support | 21 | 4 | 0.667 |
| SAME_CHECK_HOOK / split_prefix_flag | 49 | 0 | 0.612 |
| SAME_CHECK_HOOK / split_suffix_flag | 40 | 0 | 0.375 |
| SAME_CHECK_HOOK / split_temporal_flag_records | 6 | 0 | 0.833 |

Representative serialized parent/child circuits, witnesses, provenance and comparisons are in `results/v0.2/examples/`. They can be replayed with `ftqec verify`.

- `local-quality-repair` from `css4-X-seed0-cegis.json`: independent_full_interval_flag, parent lower bound 1 -> child 2; source-witness elimination=True, quality success=True.
- `witness-only-repair` from `css4-X-seed0-cegis.json`: split_prefix_flag, parent lower bound 1 -> child 1; source-witness elimination=True, quality success=False.

The absence of overall improvement has several concrete explanations. Non-CSS product readout supplies vulnerable terminal records outside this extraction-repair library. The four-qubit CSS example has limited attainable quality, while the successful Steane seed already starts at the target. Moreover, repairs that eliminate one witness without improving the certified distance/resources can be dominated and removed from the finite beam, preventing accumulation of neutral intermediate repairs across checks. These observations motivate future readout synthesis, multi-witness constraint retention and larger predeclared pilots; they do not justify retuning or claiming this pilot positive.

## Decoder-dependent failures

Every candidate also trains/evaluates the deterministic detector-to-logical recovery baseline through weight one. Raw `decoder` records preserve coverage, resolved cases, failures and example nonzero-syndrome collisions. These counts are separate from circuit distance and are not LER estimates. Tie choices can cause decoder failure even with nonzero detectors; a dedicated regression demonstrates the distinction.

## Performance and verification

Three repeated-round Steane circuits were profiled using both the original forward single-fault path and the new suffix-map path, each three times, with exact signature equality. Median speedups:

- `aac259b9dff50156609d`: 1267 elementary variants, 157 IR operations; 35.55x; forward median 0.212396s -> suffix median 0.005974s.
- `ada6bc5645b00ca78fe6`: 1981 elementary variants, 241 IR operations; 48.01x; forward median 0.497524s -> suffix median 0.010362s.
- `3feee3526676a0f0e3ea`: 1879 elementary variants, 229 IR operations; 50.65x; forward median 0.457277s -> suffix median 0.009028s.

The final profile now spreads cost over signature enumeration, JSON/dataclass serialization, IR validation and search bookkeeping. Packed suffix maps remove the demonstrated repeated-propagation bottleneck. High-weight scaling and larger-code throughput remain unmeasured; no held-out execution is used to support a performance claim.

Full suite: 74 passed, 0 failures, 0 skips. All 96 raw runs validate against the native V0.2 schema, and all 2281 reported witness instances replay independently from rebuilt serialized circuits. Dense-state tests cover repeated CSS/non-CSS semantics, actual measurement/reset outcomes, flags, preparation-output noise and both logical memory bases. Full editable installation and CLI paths are tested without manually setting PYTHONPATH.

## Held-out readiness gate

- Correctness: passing tests, independent temporal semantics checks, independently verified witnesses under the explicitly limited model.
- Search: no observed strongest-distance or target-reach advantage; not statistically established. Three seeds are a pilot, not broad evidence.
- Performance: practical small-development-code evaluation throughput; held-out-size scaling untested.
- Isolation: no held-out code was run, no final architecture packages imported, and no external optimal-architecture search performed. The held-out directory contains only its original README.

**NOT_READY_FOR_HELD_OUT.** Preserve the frozen research targets. The next development work should address final readout and accumulation of useful witness-eliminating intermediate candidates, then test a new, predeclared multi-seed protocol.
