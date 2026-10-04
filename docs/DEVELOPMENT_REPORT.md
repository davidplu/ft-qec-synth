# V0.1 development report

The package implements stabilizer/logical algebra, an independent circuit IR, generic controlled-P flag gadgets, seeded candidate generation/mutation, greedy scheduling, resource accounting, linear Pauli fault signatures, bounded meet-in-the-middle fault search, counterexamples and Pareto beam search. No held-out architecture answers were used.

Configuration: 24 distinct candidates per code, seed 20261003, maximum weight 2, 500000 work entries per layer, idles disabled, required detection distance 2. The development suite is profiled, so its timing includes profiling overhead.

| Code | Evaluated | A rejected | B rejected | C rejected | D rejected | Frontier | Seconds |
|---|---:|---:|---:|---:|---:|---:|---:|
| Four-qubit CSS | 24 | 0 | 22 | 0 | 0 | 2 | 0.512 |
| Four-qubit non-CSS development example | 24 | 0 | 22 | 0 | 0 | 2 | 0.638 |
| Five-qubit perfect code | 24 | 0 | 0 | 0 | 0 | 2 | 1.492 |
| Three-qubit repetition | 24 | 0 | 24 | 0 | 0 | 0 | 0.353 |
| Steane CSS | 24 | 0 | 0 | 0 | 0 | 3 | 3.376 |

All 120 candidates were evaluated in 6.371 seconds summed across codes. C found weight-two witnesses in every candidate that survived B; these meet the default threshold and are not rejections. D was unnecessary once those upper bounds were known. All accepted development-frontier candidates have exact detection distance 2 under this boundary model. The repetition example has a weight-one logical Z and correctly yields an empty accepted frontier.

Representative resource tradeoffs (Q, D, QD, two-qubit gates):

- Four-qubit CSS, `728cb80cd589a5c92cc9`: (9, 24, 216, 14).
- Four-qubit CSS, `fc2f3dd0f98d85bc21e1`: (7, 32, 224, 16).
- Four-qubit non-CSS development example, `762943b14b3dcf94b3b0`: (9, 32, 288, 14).
- Four-qubit non-CSS development example, `dfa20d8aa4793a944881`: (7, 40, 280, 16).
- Five-qubit perfect code, `f1a4596800cfe2771f8d`: (6, 32, 192, 16).
- Five-qubit perfect code, `298192c4d2e14693f4a0`: (11, 24, 264, 20).
- Steane CSS, `aac259b9dff50156609d`: (8, 48, 384, 24).
- Steane CSS, `22a37fe942da3dcc0ef9`: (17, 25, 425, 32).
- Steane CSS, `ccb443e3ace4edfeb3d5`: (14, 28, 392, 30).

The non-profiled 1000-candidate Steane run used seed 7, weight 2, work limit 2000000 and the same acceptance threshold: 1000 evaluated in 36.374 seconds (27.5 candidates/second), 6 frontier objective vectors, 0 rejections. Saved in `results/steane-budget1000.json`. This is small-code local throughput, not a scaling claim for larger held-out codes.

The 1000-candidate trial exposed repeated full-frontier recomputation; the final implementation updates frontiers incrementally and prunes identical objective vectors. Every architecture remains in the raw result records. Final development profile:

- signatures: 5.797 cumulative seconds. These times are nested, not additive.
- propagate: 4.035 cumulative seconds. These times are nested, not additive.
- conjugate: 2.371 cumulative seconds. These times are nested, not additive.

Signature construction is the main remaining cost. Suffix propagation maps are the first V0.2 performance priority. No multiprocessing or external simulator is required.

Verification: 33 tests executed, 32 passed and one optional JSON-schema validation test skipped because jsonschema is not installed in the bundled runtime. The optional `verification` extra enables it. Dense-matrix checks independently verify all unitary Clifford propagation; a separate boolean-array simulator checks multi-fault/idle signature linearity. Algebra, true distance-two/three cases, work limits, physical-location exclusions, scheduling, resources, deterministic search, staged rejection and CLI integration are tested. The wheel was built and installed into a workspace-local smoke-test folder; its CLI validated the Steane input successfully.

Ready for held-out evaluation: stabilizer-only JSON input; n/rank/k/commutation and generic logical basis; generic bounded candidate generation and beam mutations; JSON circuit/candidate serialization; schedule and resource metrics; configured single-round ideal-boundary fault screening through weight 1/2/3 with explicit limits and witnesses; machine-readable acceptance/rejection records and Pareto exports; reproducible seeds/input hashes/source-version fields.

Not ready: full FT recovery/correction certification, repeated noisy-round distance, globally optimal architectures, high-distance exact certification, hardware routing or LER comparison. Generating-basis search and independent partial-check measurements are not implemented. See the limitations and roadmap. The software git commit is null in this non-git directory; preserve the source package alongside the results.
