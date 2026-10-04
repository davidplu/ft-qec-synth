# Development Suite 2

6 primary code/basis tasks selected from 23 code instances. All are permanently development inputs. Shared parents and basis tasks are not independent families.

| Task | n | k | CSS generators | d code | initial | boundary | target |
|---|---:|---:|---|---:|---:|---:|---:|
| affine15_k1-X | 15 | 1 | True | 3 | 2 | 3 | 3 |
| steane14_sum-Z | 14 | 2 | True | 3 | 2 | 3 | 3 |
| steane7-X | 7 | 1 | True | 3 | 2 | 3 | 3 |
| simplex15_k7-X | 15 | 7 | True | 3 | 2 | 3 | 3 |
| steane7_mixed-X | 7 | 1 | False | 3 | 2 | 3 | 3 |
| simplex15_k7-Z | 15 | 7 | True | 3 | 2 | 3 | 3 |

The manifest includes full check weights, qubit degrees, overlap matrices, spectrum calibration and provenance. Mechanism coverage is a deterministic representative sample, not an exhaustive absence test. The Shor row/column distance argument and exhaustive code-distance results are retained in candidate_pool.json. Non-CSS generator controls represent an existing CSS stabilizer group, not a genuinely different construction.

Final comparison: ten new seeds (10–19), 32 evaluations per arm following the documented pre-comparison compute amendment, fixed 200000 certification/spectrum caps and all other frozen V0.3 parameters. Ablations are secondary three-seed comparisons. Pilots use only random/resource arms (seeds 6,7) plus predetermined fully flagged constructions. No pilot candidate is supplied to final initial populations.

Rejected and deferred tasks:

| Task | Screen | Difficulty | Pilot |
|---|---|---|---|
| steane7-Z | BOUNDARY_LIMITED | TOO_EASY | not eligible |
| steane7_mixed-Z | BOUNDARY_LIMITED | TOO_EASY | not eligible |
| steane14_sum-X | BOUNDARY_LIMITED | TOO_EASY | not eligible |
| shor3x3-X | BOUNDARY_LIMITED | TOO_EASY | not eligible |
| shor3x3-Z | BOUNDARY_LIMITED | TOO_EASY | not eligible |
| shor3x4-X | BOUNDARY_LIMITED | TOO_EASY | not eligible |
| shor3x4-Z | UNRESOLVED | TOO_EASY | not eligible |
| shor3x5-X | BOUNDARY_LIMITED | TOO_EASY | not eligible |
| shor3x5-Z | UNRESOLVED | TOO_EASY | not eligible |
| shor4x4-X | OPEN_HEADROOM | CERTIFICATION_TIER_LIMITED | not eligible |
| shor4x4-Z | OPEN_HEADROOM | CERTIFICATION_TIER_LIMITED | not eligible |
| shor4x5-X | OPEN_HEADROOM | CERTIFICATION_TIER_LIMITED | not eligible |
| shor4x5-Z | OPEN_HEADROOM | CERTIFICATION_TIER_LIMITED | not eligible |
| shor5x5-X | OPEN_HEADROOM | CERTIFICATION_TIER_LIMITED | not eligible |
| shor5x5-Z | OPEN_HEADROOM | CERTIFICATION_TIER_LIMITED | not eligible |
| shor3x3_mixed-X | BOUNDARY_LIMITED | TOO_EASY | not eligible |
| shor3x3_mixed-Z | BOUNDARY_LIMITED | TOO_EASY | not eligible |
| grid3-X | BOUNDARY_LIMITED | TOO_EASY | not eligible |
| grid3-Z | BOUNDARY_LIMITED | TOO_EASY | not eligible |
| grid4-X | OPEN_HEADROOM | CERTIFICATION_TIER_LIMITED | not eligible |
| grid4-Z | OPEN_HEADROOM | CERTIFICATION_TIER_LIMITED | not eligible |
| grid5-X | OPEN_HEADROOM | CERTIFICATION_TIER_LIMITED | not eligible |
| grid5-Z | OPEN_HEADROOM | CERTIFICATION_TIER_LIMITED | not eligible |
| affine15_k1-Z | UNRESOLVED | TOO_EASY | not eligible |
| perfect5-X | BOUNDARY_LIMITED | UNREACHABLE/UNKNOWN | not eligible |
| perfect5-Z | BOUNDARY_LIMITED | UNREACHABLE/UNKNOWN | not eligible |
| noncss4-X | BOUNDARY_LIMITED | UNREACHABLE/UNKNOWN | not eligible |
| noncss4-Z | BOUNDARY_LIMITED | UNREACHABLE/UNKNOWN | not eligible |
| shor7x7-X | COMPUTE_DEFERRED | UNREACHABLE/UNKNOWN | not eligible |
| shor7x7-Z | COMPUTE_DEFERRED | UNREACHABLE/UNKNOWN | not eligible |
| grid3_dense-X | BOUNDARY_LIMITED | TOO_EASY | not eligible |
| grid3_dense-Z | BOUNDARY_LIMITED | TOO_EASY | not eligible |
| grid4_dense-X | OPEN_HEADROOM | CERTIFICATION_TIER_LIMITED | not eligible |
| grid4_dense-Z | OPEN_HEADROOM | CERTIFICATION_TIER_LIMITED | not eligible |
| grid5_dense-X | OPEN_HEADROOM | CERTIFICATION_TIER_LIMITED | not eligible |
| grid5_dense-Z | OPEN_HEADROOM | CERTIFICATION_TIER_LIMITED | not eligible |
| shor4x4_dense-X | OPEN_HEADROOM | CERTIFICATION_TIER_LIMITED | not eligible |
| shor4x4_dense-Z | OPEN_HEADROOM | CERTIFICATION_TIER_LIMITED | not eligible |
| affine15_k1_mixed-X | OPEN_HEADROOM | USEFUL | UNKNOWN_AFTER_BOUNDED_PILOT |
| affine15_k1_mixed-Z | UNRESOLVED | TOO_EASY | not eligible |

Selection limitation: only six tasks, below the preferred eight to fifteen, survive all criteria. They span three parent code instances and two construction families; primary code distances are all three. Higher-distance, degenerate and cyclic candidates remain in the pool/secondary suite. Genuinely non-CSS legacy codes fail product-readout screening. The non-CSS primary generator representation is a control, not a new non-CSS stabilizer family. k>1 evaluations protect only logical index zero in the chosen basis.

Independent initial calibration audited 180 initial architectures and found 31 hidden tier-three initial architectures in three large-code tasks. Those are deferred under the original target rule, so native certificate censoring is not mistaken for architecture headroom. The pre-audit screen is retained. Original and additional pilots, including role-based reachability checks and all failures, are saved separately; no pilot configuration is passed to the final search.

Every admitted task has a native-engine target lower bound of three on a saved generic pilot architecture and independent exhaustive exclusion through weight two. Every calibration population remains below the target even after independent resolution. The final manifest was selected without any V0.3 strategy result.

## Reproduce the frozen comparison

Use the repository's installed Python environment. From the repository root:

```text
python experiments/compare_development_v2.py run
python experiments/compare_development_v2.py audit
python experiments/verify_development_v2_archive.py
python experiments/report_development_v2.py
```

The first command resumes from existing lossless raw files and checks protocol hashes, matched initial populations and fixed evaluation-slot counts. Remove or relocate the new comparison raw directory only when intentionally reproducing the entire experiment. Do not rerun pool construction, calibration, pilots or manifest selection to interpret the frozen comparison. Those stages have their own preserved pre-comparison evidence.

The audit independently replays physical witnesses and spectrum representatives, verifies nontrivial exclusions and resolves censored initial populations without feeding any result back into search. Primary endpoints use native frozen-engine bounds. Independent certificates and population diagnostics remain separately labeled. The results report contains all twenty requested answers; machine-readable paired tests, wall-clock checkpoints, ancestry, ablations, operator statistics and readiness are under `results/development_v2`.

Archive verification checks every raw hash, exact configuration, code input and matched population. Freeze checks are byte-level: retain the original line endings rather than regenerate hash records after a converted checkout. The delivery ZIP preserves the worktree bytes and excludes local environments, caches and Git internals.

Git attributes preserve the bytes of hash-controlled source, protocols, inputs and results across checkouts. The byte-identical historical V0.3 audit checkpoint is also tracked because the pre-design freeze includes its hash. This packaging correction changes neither runtime behavior nor scientific evidence.
