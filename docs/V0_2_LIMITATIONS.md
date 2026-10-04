# V0.2 limits and held-out gate

- Repeated extraction uses a specified ideal encoded logical eigenstate, optional local output-preparation noise, noisy ancilla preparation/reset and noisy final physical readout. It does not synthesize or fault-test an encoding/preparation circuit.
- One logical index and X or Z memory are tested per experiment. k>1 codes require separate runs for all desired indices/bases. The development comparison tests index 0 only.
- Product-basis destructive readout closes the entire locally compatible stabilizer subgroup, including inferred signed products. Non-CSS codes can have a weight-one readout ceiling. Such a result is valid for this experiment but does not characterize the code's attainable distance with a richer logical readout circuit.
- Measurement noise is classical readout flipping; separate quantum measurement backaction faults are not included. Noise is adversarial location-weighted Pauli enumeration, not a calibrated stochastic LER model.
- Logical decoder recovery is a detector-to-logical correction interface, not a synthesized physical correction circuit. Minimum weights are certified only through completely enumerated training layers. Unseen/partially covered signatures remain unresolved.
- Searches are exact when completed. Hash searches cover weights 1–3; direct signature-combination enumeration covers tractable weights 4–6. Work limits never certify partial layers. Above the cutoff, no claim is made.
- Flag/order/reuse repairs can eliminate one witness without eliminating equally low-weight alternatives. The library does not jointly accumulate all previous counterexamples as synthesis constraints or repair terminal readout/encoding.
- Source witness transport is semantic rather than a proof of identical physical time coordinates. Idle or ambiguous removed locations are not credited as eliminated.
- The fixed generating basis, unit-time greedy scheduling and finite beam/gadget family remain limited. There is no global optimum, hardware router, adaptive extraction or high-statistics LER.
- The three-seed, 24-slot experiment is a small controlled pilot. It cannot establish a general CEGIS advantage; code/basis cohorts must not be pooled as independent statistical samples.

No held-out code is run in V0.2. The readiness verdict in `V0_2_RESULTS.md` considers correctness, empirical search advantage, practical throughput and isolation separately. Working software is not sufficient evidence to spend the held-out benchmark.
