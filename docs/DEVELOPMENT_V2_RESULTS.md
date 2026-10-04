# Development Suite 2 results

NOT_READY_FOR_HELD_OUT

V0.3 shows partial development success, without passing the frozen general-advantage criterion. Target totals out of 60: {'random': 6, 'resource': 1, 'v02': 7, 'v03': 14, 'mixed': 10}. More observed successes are not automatically statistically validated superiority. The RANDOM/RESOURCE matched-QD tests favor the baselines, not V0.3.

Terminal ceilings alone cannot explain the remaining readiness failure: all primary tasks have independently certified reachable headroom, and 59 of 60 final initial populations have no target. However, this related, small finite suite and the fixed 32-slot budget do not support a causal verdict that the guidance method is ineffective in general.

The benchmark manifest and complete experiment driver were committed as 6035a868a120f7a23e907d687b9c9f5e08b5e62a before the first primary run. The frozen runtime baseline is 50b926c793bbc78fa922c5eebf067678fec29504. Manifest SHA256: 0686826aedce8c76e827e003c85789b2c5b217481d8ac174ddf6be792efec818.

Final comparison: 390 runs and 12,480 evaluation slots, six tasks, ten primary seeds (10–19), five primary arms and five secondary ablations on seeds 10–12. Each run uses 32 slots; unreached targets receive penalized evaluation count 33. The retained initial 64-slot proposal was replaced by the documented compute-only amendment before primary results. Pilots retained 64 slots.

The V0.3 runtime source and all original results are byte-identical to the pre-design freeze. New inputs are permanently development. No held-out input, architecture or resource count was used. Final seeds differ from calibration and pilots. All raw final runs, initial spectra, rejected candidates and reachability pilots are saved separately.

Selection follows DEVELOPMENT_V2_SELECTION_PROTOCOL.md and the prospectively committed structural pool extension. Manifest and hypothesis hashes are checked before every run. Candidate distances use explicit construction proofs or exhaustive Pauli checks; terminal ceilings use physical replay and exhaustive classical parity supports. A terminal-only distance is an upper bound on a full circuit, never its lower bound.

Distance claims concern the frozen chosen-basis logical-index-zero memory experiment. In k>1 tasks, protection of every encoded logical observable is not established. Circuit candidates still extract all supplied checks. Sign-flip tests assume symmetric/exchangeable seed-block differences under the null; they are not a randomized causal trial.

Considered 23 code instances and 46 basis tasks. Selected 6 tasks from 5 named check sets, 3 parent instances and 2 declared construction groups. Both groups are Hamming-related; their labels do not establish independent sampling of code families. Non-CSS generator controls and direct sums have shared dependence. Mixed unsigned presentations preserve the binary stabilizer module and distance but can change the joint eigensector. The suite does not establish generalization to arbitrary non-CSS stabilizer groups.

Primary check weights are 4, 6 and 8. The desired weight-3/5, higher-distance, cyclic-in-the-supplied-order and strongly degenerate primary strata are absent. Such coverage cannot be inferred from deferred candidates. Six tasks survived the fixed criteria, below the preferred eight to fifteen. Independent calibration found 31 hidden target architectures and deferred three large-code tasks rather than treating certificate censoring as genuine architecture headroom.

| Task | n,k | code d | initial | boundary | target | CSS representation |
|---|---|---:|---:|---:|---:|---|
| affine15_k1-X | 15,1 | 3 | 2 | 3 | 3 | True |
| steane14_sum-Z | 14,2 | 3 | 2 | 3 | 3 | True |
| steane7-X | 7,1 | 3 | 2 | 3 | 3 | True |
| simplex15_k7-X | 15,7 | 3 | 2 | 3 | 3 | True |
| steane7_mixed-X | 7,1 | 3 | 2 | 3 | 3 | False |
| simplex15_k7-Z | 15,7 | 3 | 2 | 3 | 3 | True |

Rejected/deferred candidate tasks:

| Task | Screen | Difficulty |
|---|---|---|
| steane7-Z | BOUNDARY_LIMITED | TOO_EASY |
| steane7_mixed-Z | BOUNDARY_LIMITED | TOO_EASY |
| steane14_sum-X | BOUNDARY_LIMITED | TOO_EASY |
| shor3x3-X | BOUNDARY_LIMITED | TOO_EASY |
| shor3x3-Z | BOUNDARY_LIMITED | TOO_EASY |
| shor3x4-X | BOUNDARY_LIMITED | TOO_EASY |
| shor3x4-Z | UNRESOLVED | TOO_EASY |
| shor3x5-X | BOUNDARY_LIMITED | TOO_EASY |
| shor3x5-Z | UNRESOLVED | TOO_EASY |
| shor4x4-X | OPEN_HEADROOM | CERTIFICATION_TIER_LIMITED |
| shor4x4-Z | OPEN_HEADROOM | CERTIFICATION_TIER_LIMITED |
| shor4x5-X | OPEN_HEADROOM | CERTIFICATION_TIER_LIMITED |
| shor4x5-Z | OPEN_HEADROOM | CERTIFICATION_TIER_LIMITED |
| shor5x5-X | OPEN_HEADROOM | CERTIFICATION_TIER_LIMITED |
| shor5x5-Z | OPEN_HEADROOM | CERTIFICATION_TIER_LIMITED |
| shor3x3_mixed-X | BOUNDARY_LIMITED | TOO_EASY |
| shor3x3_mixed-Z | BOUNDARY_LIMITED | TOO_EASY |
| grid3-X | BOUNDARY_LIMITED | TOO_EASY |
| grid3-Z | BOUNDARY_LIMITED | TOO_EASY |
| grid4-X | OPEN_HEADROOM | CERTIFICATION_TIER_LIMITED |
| grid4-Z | OPEN_HEADROOM | CERTIFICATION_TIER_LIMITED |
| grid5-X | OPEN_HEADROOM | CERTIFICATION_TIER_LIMITED |
| grid5-Z | OPEN_HEADROOM | CERTIFICATION_TIER_LIMITED |
| affine15_k1-Z | UNRESOLVED | TOO_EASY |
| perfect5-X | BOUNDARY_LIMITED | UNREACHABLE/UNKNOWN |
| perfect5-Z | BOUNDARY_LIMITED | UNREACHABLE/UNKNOWN |
| noncss4-X | BOUNDARY_LIMITED | UNREACHABLE/UNKNOWN |
| noncss4-Z | BOUNDARY_LIMITED | UNREACHABLE/UNKNOWN |
| shor7x7-X | COMPUTE_DEFERRED | UNREACHABLE/UNKNOWN |
| shor7x7-Z | COMPUTE_DEFERRED | UNREACHABLE/UNKNOWN |
| grid3_dense-X | BOUNDARY_LIMITED | TOO_EASY |
| grid3_dense-Z | BOUNDARY_LIMITED | TOO_EASY |
| grid4_dense-X | OPEN_HEADROOM | CERTIFICATION_TIER_LIMITED |
| grid4_dense-Z | OPEN_HEADROOM | CERTIFICATION_TIER_LIMITED |
| grid5_dense-X | OPEN_HEADROOM | CERTIFICATION_TIER_LIMITED |
| grid5_dense-Z | OPEN_HEADROOM | CERTIFICATION_TIER_LIMITED |
| shor4x4_dense-X | OPEN_HEADROOM | CERTIFICATION_TIER_LIMITED |
| shor4x4_dense-Z | OPEN_HEADROOM | CERTIFICATION_TIER_LIMITED |
| affine15_k1_mixed-X | OPEN_HEADROOM | USEFUL |
| affine15_k1_mixed-Z | UNRESOLVED | TOO_EASY |

Failure-mechanism coverage (sampled representatives):

| Task | Observed mechanisms |
|---|---|
| affine15_k1-X | CROSS_CHECK_COLLISION:606, CROSS_CHECK_OVERLAP:281, FINAL_READOUT:14, INTERACTION_ORDER_HOOK:887, SAME_CHECK_HOOK:91 |
| steane14_sum-Z | CROSS_CHECK_COLLISION:830, CROSS_CHECK_OVERLAP:88, FINAL_READOUT:23, INTERACTION_ORDER_HOOK:918, SAME_CHECK_HOOK:23 |
| steane7-X | CROSS_CHECK_COLLISION:719, CROSS_CHECK_OVERLAP:127, FINAL_READOUT:38, INTERACTION_ORDER_HOOK:846, SAME_CHECK_HOOK:103 |
| simplex15_k7-X | CROSS_CHECK_COLLISION:558, CROSS_CHECK_OVERLAP:210, FINAL_READOUT:30, FLAG_CANCELLATION:30, INTERACTION_ORDER_HOOK:768, SAME_CHECK_HOOK:268 |
| steane7_mixed-X | CROSS_CHECK_COLLISION:877, CROSS_CHECK_OVERLAP:120, FINAL_READOUT:28, INTERACTION_ORDER_HOOK:997, SAME_CHECK_HOOK:74 |
| simplex15_k7-Z | CROSS_CHECK_COLLISION:614, CROSS_CHECK_OVERLAP:182, FINAL_READOUT:14, FLAG_CANCELLATION:95, FLAG_READOUT_HIDING:4, INTERACTION_ORDER_HOOK:796, SAME_CHECK_HOOK:241 |

Final strategy results use native frozen-engine bounds. Initial-target counts are retained, never removed after selection; independent resolution is a separate column. Ablation rows have three seeds, primary rows ten.

| Task | Strategy | targets/runs | native initial targets | independent initial targets | mean d lower | penalized evaluations | seconds/run |
|---|---|---:|---:|---:|---:|---:|---:|
| affine15_k1-X | random | 0/10 | 0 | 0 | 2.00 | 33.00 | 9.98 |
| affine15_k1-X | resource | 0/10 | 0 | 0 | 2.00 | 33.00 | 7.45 |
| affine15_k1-X | v02 | 0/10 | 0 | 0 | 2.00 | 33.00 | 9.82 |
| affine15_k1-X | v03 | 0/10 | 0 | 0 | 2.00 | 33.00 | 13.20 |
| affine15_k1-X | mixed | 0/10 | 0 | 0 | 2.00 | 33.00 | 12.93 |
| affine15_k1-X | v03_raw | 0/3 | 0 | 0 | 2.00 | 33.00 | 13.33 |
| affine15_k1-X | v03_signature | 0/3 | 0 | 0 | 2.00 | 33.00 | 12.51 |
| affine15_k1-X | v03_no_protection | 0/3 | 0 | 0 | 2.00 | 33.00 | 14.43 |
| affine15_k1-X | v03_arbitrary | 0/3 | 0 | 0 | 2.00 | 33.00 | 12.77 |
| affine15_k1-X | v03_no_coverage | 0/3 | 0 | 0 | 2.00 | 33.00 | 13.70 |
| steane14_sum-Z | random | 2/10 | 1 | 1 | 2.20 | 27.80 | 6.59 |
| steane14_sum-Z | resource | 1/10 | 1 | 1 | 2.10 | 30.10 | 4.74 |
| steane14_sum-Z | v02 | 5/10 | 1 | 1 | 2.50 | 20.70 | 7.16 |
| steane14_sum-Z | v03 | 3/10 | 1 | 1 | 2.30 | 28.80 | 8.25 |
| steane14_sum-Z | mixed | 5/10 | 1 | 1 | 2.50 | 27.50 | 8.12 |
| steane14_sum-Z | v03_raw | 2/3 | 1 | 1 | 2.67 | 22.67 | 8.03 |
| steane14_sum-Z | v03_signature | 1/3 | 1 | 1 | 2.33 | 23.33 | 7.77 |
| steane14_sum-Z | v03_no_protection | 1/3 | 1 | 1 | 2.33 | 23.33 | 8.65 |
| steane14_sum-Z | v03_arbitrary | 1/3 | 1 | 1 | 2.33 | 23.33 | 8.24 |
| steane14_sum-Z | v03_no_coverage | 3/3 | 1 | 1 | 3.00 | 6.67 | 9.25 |
| steane7-X | random | 2/10 | 0 | 0 | 2.20 | 29.90 | 2.20 |
| steane7-X | resource | 0/10 | 0 | 0 | 2.00 | 33.00 | 1.39 |
| steane7-X | v02 | 1/10 | 0 | 0 | 2.10 | 30.50 | 2.39 |
| steane7-X | v03 | 5/10 | 0 | 0 | 2.50 | 26.40 | 3.30 |
| steane7-X | mixed | 2/10 | 0 | 0 | 2.20 | 29.70 | 3.18 |
| steane7-X | v03_raw | 2/3 | 0 | 0 | 2.67 | 22.33 | 3.19 |
| steane7-X | v03_signature | 0/3 | 0 | 0 | 2.00 | 33.00 | 2.54 |
| steane7-X | v03_no_protection | 1/3 | 0 | 0 | 2.33 | 29.33 | 3.06 |
| steane7-X | v03_arbitrary | 3/3 | 0 | 0 | 3.00 | 22.00 | 2.85 |
| steane7-X | v03_no_coverage | 1/3 | 0 | 0 | 2.33 | 25.00 | 3.13 |
| simplex15_k7-X | random | 1/10 | 0 | 0 | 2.10 | 30.60 | 5.98 |
| simplex15_k7-X | resource | 0/10 | 0 | 0 | 2.00 | 33.00 | 4.09 |
| simplex15_k7-X | v02 | 0/10 | 0 | 0 | 2.00 | 33.00 | 6.56 |
| simplex15_k7-X | v03 | 1/10 | 0 | 0 | 2.10 | 31.80 | 8.48 |
| simplex15_k7-X | mixed | 0/10 | 0 | 0 | 2.00 | 33.00 | 8.03 |
| simplex15_k7-X | v03_raw | 0/3 | 0 | 0 | 2.00 | 33.00 | 8.05 |
| simplex15_k7-X | v03_signature | 0/3 | 0 | 0 | 2.00 | 33.00 | 7.78 |
| simplex15_k7-X | v03_no_protection | 0/3 | 0 | 0 | 2.00 | 33.00 | 8.41 |
| simplex15_k7-X | v03_arbitrary | 0/3 | 0 | 0 | 2.00 | 33.00 | 7.30 |
| simplex15_k7-X | v03_no_coverage | 0/3 | 0 | 0 | 2.00 | 33.00 | 7.24 |
| steane7_mixed-X | random | 1/10 | 0 | 0 | 2.10 | 31.90 | 2.35 |
| steane7_mixed-X | resource | 0/10 | 0 | 0 | 2.00 | 33.00 | 1.51 |
| steane7_mixed-X | v02 | 1/10 | 0 | 0 | 2.10 | 30.50 | 2.52 |
| steane7_mixed-X | v03 | 3/10 | 0 | 0 | 2.30 | 31.00 | 3.41 |
| steane7_mixed-X | mixed | 2/10 | 0 | 0 | 2.20 | 31.20 | 3.16 |
| steane7_mixed-X | v03_raw | 2/3 | 0 | 0 | 2.67 | 28.00 | 3.06 |
| steane7_mixed-X | v03_signature | 0/3 | 0 | 0 | 2.00 | 33.00 | 2.76 |
| steane7_mixed-X | v03_no_protection | 1/3 | 0 | 0 | 2.33 | 29.67 | 3.53 |
| steane7_mixed-X | v03_arbitrary | 0/3 | 0 | 0 | 2.00 | 33.00 | 3.25 |
| steane7_mixed-X | v03_no_coverage | 2/3 | 0 | 0 | 2.67 | 27.00 | 3.03 |
| simplex15_k7-Z | random | 0/10 | 0 | 0 | 2.00 | 33.00 | 5.98 |
| simplex15_k7-Z | resource | 0/10 | 0 | 0 | 2.00 | 33.00 | 4.11 |
| simplex15_k7-Z | v02 | 0/10 | 0 | 0 | 2.00 | 33.00 | 6.29 |
| simplex15_k7-Z | v03 | 2/10 | 0 | 0 | 2.20 | 31.90 | 8.93 |
| simplex15_k7-Z | mixed | 1/10 | 0 | 0 | 2.10 | 32.90 | 8.40 |
| simplex15_k7-Z | v03_raw | 0/3 | 0 | 0 | 2.00 | 33.00 | 8.94 |
| simplex15_k7-Z | v03_signature | 0/3 | 0 | 0 | 2.00 | 33.00 | 7.76 |
| simplex15_k7-Z | v03_no_protection | 0/3 | 0 | 0 | 2.00 | 33.00 | 9.18 |
| simplex15_k7-Z | v03_arbitrary | 0/3 | 0 | 0 | 2.00 | 33.00 | 7.28 |
| simplex15_k7-Z | v03_no_coverage | 2/3 | 0 | 0 | 2.67 | 29.00 | 8.32 |

Paired confirmatory tests. Positive difference favors V0.3; QD differences are absolute QD saved. Seed blocks contain all tasks, with family-block sensitivity and two-level bootstrap intervals. Small family counts sharply limit generalization.

| Baseline | Endpoint | W/T/L | effect | 95% interval | Holm p | family sensitivity p | passes |
|---|---|---|---:|---|---:|---:|---|
| random | target | 9/50/1 | 0.13333333333333333 | [0, 0.26] | 0.6562 | 1.0000 | False |
| random | evaluations | 10/46/4 | 0.55 | [-1, 2.2] | 1.0000 | 1.0000 | False |
| random | distance | 9/50/1 | 0.13333333333333333 | [0, 0.26] | 0.6562 | 1.0000 | False |
| random | qd | 6/27/27 | -330.1333333333333 | [-906.6, -142.8] | 0.0234 | 0.5000 | False |
| resource | target | 13/47/0 | 0.21666666666666667 | [0, 0.32] | 0.0781 | 1.0000 | False |
| resource | evaluations | 13/47/0 | 2.033333333333333 | [0, 3.2] | 0.0781 | 1.0000 | False |
| resource | distance | 13/47/0 | 0.21666666666666667 | [0, 0.32] | 0.0781 | 1.0000 | False |
| resource | qd | 2/9/49 | -434.18333333333334 | [-806.1, -318.1] | 0.0234 | 0.5000 | False |
| v02 | target | 13/41/6 | 0.11666666666666667 | [0, 0.23333333333333334] | 0.6562 | 1.0000 | False |
| v02 | evaluations | 13/41/6 | -0.36666666666666664 | [-2.1666666666666665, 1.16] | 1.0000 | 1.0000 | False |
| v02 | distance | 13/41/6 | 0.11666666666666667 | [0, 0.23333333333333334] | 0.6562 | 1.0000 | False |
| v02 | qd | 9/37/14 | -35.9 | [-315.2, 121.2] | 0.6562 | 0.5000 | False |

Observed composition is not proof that the repairs were necessary. Full ancestry, architecture IDs, M sequences, d sequences and resource changes are in composition.json.

| Strategy | gain events | neutral-reduction compositions | strict guided | beyond initial compositions |
|---|---:|---:|---:|---:|
| random | 10 | 0 | 0 | 0 |
| resource | 0 | 0 | 0 | 0 |
| v02 | 48 | 1 | 1 | 1 |
| v03 | 21 | 11 | 9 | 11 |
| mixed | 21 | 6 | 5 | 5 |

Expanded-node gradient association (observational, exposure-confounded):

| Strategy | class reduction | edges | later gains | fraction |
|---|---|---:|---:|---:|
| random | False | 333 | 14 | 0.042042042042042045 |
| random | True | 61 | 0 | 0.0 |
| resource | False | 864 | 0 | 0.0 |
| resource | True | 67 | 0 | 0.0 |
| v02 | False | 85 | 13 | 0.15294117647058825 |
| v02 | True | 43 | 1 | 0.023255813953488372 |
| v03 | False | 127 | 4 | 0.031496062992125984 |
| v03 | True | 251 | 23 | 0.09163346613545817 |
| mixed | False | 177 | 7 | 0.03954802259887006 |
| mixed | True | 248 | 11 | 0.04435483870967742 |

Runtime/scaling; examined-combination rates refer to bounded certification, not all possible combinations. Capped third-weight searches cannot establish completion. Wall-clock checkpoints include analysis overhead and are saved in wall_clock_comparison.json. Process peaks include earlier runs in the same driver process.

| Task | n | checks | slots/s | unique arch/s | fault joins/s | peak MiB |
|---|---:|---:|---:|---:|---:|---:|
| affine15_k1-X | 15 | 14 | 2.997 | 2.765 | 6134737.538680853 | 202.6 |
| steane14_sum-Z | 14 | 12 | 4.589 | 4.234 | 6084854.307476183 | 202.6 |
| steane7-X | 7 | 6 | 12.839 | 11.338 | 5541578.652801944 | 202.6 |
| simplex15_k7-X | 15 | 8 | 4.828 | 4.399 | 5030873.909088574 | 202.6 |
| steane7_mixed-X | 7 | 6 | 12.369 | 10.947 | 5393746.1150542395 | 202.6 |
| simplex15_k7-Z | 15 | 8 | 4.747 | 4.313 | 5217583.877311665 | 202.6 |

Unrelated size proxies (runtime only):

| Proxy | n | slots | search seconds | audit seconds | native lower bound | independent lower bound | peak MiB |
|---|---:|---:|---:|---:|---:|---:|---:|
| generic-shor-4x5-plus-3-fixed-qubits-proxy | 23 | 32 | 16.95 | 0.216 | 2 | 3 | 105.2 |
| generic-shor-5x5-plus-0-fixed-qubits-proxy | 25 | 32 | 242.76 | 0.521 | 2 | 3 | 141.3 |
| generic-shor-5x6-plus-1-fixed-qubits-proxy | 31 | 32 | 306.83 | 0.363 | 2 | 3 | 152.2 |
| generic-shor-6x7-plus-2-fixed-qubits-proxy | 44 | 32 | 611.74 | 0.926 | 2 | 3 | 233.5 |

Fixed-candidate fault-weight/round scaling (independent of strategy selection):

| n | rounds | requested weight | native lower/upper | examined combinations | seconds | reason |
|---|---:|---:|---|---:|---:|---|
| 23 | 1 | 1 | 2/None | 3462 | 0.058 | None |
| 23 | 1 | 2 | 2/2 | 84172 | 0.071 | None |
| 23 | 1 | 3 | 2/2 | 84172 | 0.067 | None |
| 23 | 3 | 1 | 2/None | 10340 | 0.112 | None |
| 23 | 3 | 2 | 2/None | 200000 | 0.173 | work_limit |
| 23 | 3 | 3 | 2/None | 200000 | 0.163 | work_limit |
| 25 | 1 | 1 | 2/None | 3913 | 0.055 | None |
| 25 | 1 | 2 | 2/2 | 99976 | 0.086 | None |
| 25 | 1 | 3 | 2/2 | 99976 | 0.707 | None |
| 25 | 3 | 1 | 2/None | 11689 | 0.896 | None |
| 25 | 3 | 2 | 2/None | 200000 | 0.393 | work_limit |
| 25 | 3 | 3 | 2/None | 200000 | 0.522 | work_limit |
| 31 | 1 | 1 | 2/None | 4876 | 0.336 | None |
| 31 | 1 | 2 | 2/2 | 151002 | 1.159 | None |
| 31 | 1 | 3 | 2/2 | 151002 | 1.184 | None |
| 31 | 3 | 1 | 2/None | 14566 | 1.039 | None |
| 31 | 3 | 2 | 2/None | 200000 | 2.594 | work_limit |
| 31 | 3 | 3 | 2/None | 200000 | 2.139 | work_limit |
| 44 | 1 | 1 | 2/None | 7020 | 0.520 | None |
| 44 | 1 | 2 | 2/None | 200000 | 0.787 | work_limit |
| 44 | 1 | 3 | 2/None | 200000 | 0.734 | work_limit |
| 44 | 3 | 1 | 2/None | 20972 | 2.470 | None |
| 44 | 3 | 2 | 2/None | 200000 | 3.231 | work_limit |
| 44 | 3 | 3 | 2/None | 200000 | 1.452 | work_limit |

No projection is a held-out-code measurement. Proxy checks differ in connectivity/degeneracy and exact signatures, so equal n is not equal certification cost. Targets above the frozen tier and rigorous large-distance certification remain compute-limited.

All-strategy failures: [{"task": "affine15_k1-X", "classification": "E_SEARCH_FAILED_DESPITE_CERTIFIED_REACHABLE_CANDIDATE", "independently_found_censored_target_records": 0, "alternative": "B_INSUFFICIENT_SEARCH_BUDGET remains possible; no impossibility inference", "pilot": "CONSTRUCTIVELY_REACHABLE_WITH_GENERIC_READOUT_ROLE_FLAGS"}]. Pilot witness existence distinguishes bounded search failure from impossible targets. No failed pilot proves unreachability.

Exploratory characteristics: task-wise effects and class spectra are saved. Parent-dependent representation controls, basis correlation and small family count prevent credible causal attribution to check weight, overlap, degeneracy or k. Do not promote an ablation after observing its performance.

Explicit final answers:

1. 23 candidate code instances (46 basis tasks).
2. 17 basis tasks of 11 codes were boundary-limited; this counts at least one rejected basis, not necessarily rejection of the entire code.
3. 17 basis tasks across 11 codes were already at the frozen code-distance reference goal or terminal ceiling. This is not a claim that every chosen-observable ceiling was attained: four tasks have higher terminal ceilings but initial tier three, already meeting their distance-three code reference and requiring target tier four outside the frozen primary limit. Certification-tier-limited cases are counted separately.
4. 1 task(s) rejected after all bounded reachability pilots remained unsuccessful: ['affine15_k1_mixed-X']. 2 screening tasks separately unresolved/deferred. No failed pilot proves unreachability.
5. affine15_k1-X, steane14_sum-Z, steane7-X, simplex15_k7-X, steane7_mixed-X, simplex15_k7-Z.
6. 2 declared construction groups, 3 parent instances, k values [1, 2, 7], code distances [3], check weights 4/6/8. Shared-parent controls and Hamming-related construction dependence limit diversity; genuinely non-CSS, higher-distance and cyclic primary strata are absent.
7. Every admitted task has proved terminal headroom and a certified reachable target above the calibrated initial bound. New-seed initial successes are reported separately.
8. Calibration target frequency is zero. Final independent initial audit found 1/360 target architectures; population-level frequencies per task are in the strategy table. No final task was reselected.
9. Validated general advantage versus RANDOM: False. Observed targets: 14/60 versus 6/60.
10. Validated general advantage versus RESOURCE_GUIDED: False. Observed targets: 14/60 versus 1/60.
11. Validated general advantage versus V0.2 CEGIS: False. Observed targets: 14/60 versus 7/60.
12. Passing endpoints: []. All descriptive endpoint effects and intervals are above.
13. Favorable parent-code/seed counts per endpoint: [('random', 'target', 2, 5), ('random', 'evaluations', 2, 6), ('random', 'distance', 2, 5), ('random', 'qd', 3, 6), ('resource', 'target', 2, 8), ('resource', 'evaluations', 2, 8), ('resource', 'distance', 2, 8), ('resource', 'qd', 2, 2), ('v02', 'target', 2, 8), ('v02', 'evaluations', 2, 8), ('v02', 'distance', 2, 8), ('v02', 'qd', 3, 6)]. Basis tasks and shared-parent controls are not independent codes.
14. Statistical/practical meaning requires Holm significance, practical margin and spread simultaneously; see passes column. Few independent families constrain generalization.
15. Expanded V0.3 edges with class reduction versus without: {False: (4, 127, 0.031496062992125984), True: (23, 251, 0.09163346613545817)}. Prior-suite fractions were {True: 0.04807692307692308, False: 0.04216867469879518}. Different task selection and evaluation budgets, adaptive expansion and overlapping ancestry prevent a validated prediction-improvement claim.
16. V0.3 has 9/14 strict guided compositions among gain events above the best initial tier. All gain-event composition counts: {'gains': 21, 'compositions': 11, 'guided_compositions': 9, 'gains_beyond_initial': 14, 'strict_guided_beyond_initial_compositions': 9, 'beyond_initial_compositions': 11}. These are observed histories, not proof that the intermediate repairs were necessary.
17. No reliable causal predictor established; all code-characteristic analyses are exploratory and parent-correlated.
18. Smaller-size frozen runtime gate passed: True. Actual unrelated n23/n25/n31/n44 proxy runs and independent two-fault audits were measured; these do not establish held-out distance-7/9 certification cost.
19. ALGORITHM_LIMITATION (no established general advantage at 32 slots) combined with BENCHMARK_LIMITATION (few related parents and limited seed/family power). Benchmark diversity and fixed product readout also limit generality; this experiment cannot isolate an uncapped-algorithm effect.
20. NOT_READY_FOR_HELD_OUT. Frozen reproducible advantage criterion failed.

Post-comparison diagnostic censoring audit: 0 primary record(s) had a physical target hidden by a native below-target cap. Every censored final record was independently resolved through the target exclusion tier. This audit was added while primary runs were in progress, after observing capped records; it never fed back into search or changed any confirmatory endpoint. Full certificates are in final_censoring_audit.json.

One next experiment: A prospectively fixed matched evaluation-budget staircase on the same development tasks and seeds, keeping search operators, targets and certification caps fixed, to distinguish budget insufficiency from persistent guidance failure. This is a proposed future experiment; it was not performed here.
