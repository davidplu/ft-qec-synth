# V0.2 roadmap

The V0.1 development run and saved `profile.json` identify signature construction/forward Pauli propagation as the dominant cost. Next prioritize:

1. Compute backward/suffix Clifford transfer maps once per circuit and synthesize location signatures directly; retain forward propagation as an independent oracle. Benchmark equivalence on all development circuits including resets and measurement records.
2. Add syndrome-collision correction-compatibility tests, repeated noisy extraction rounds and explicit decoder/recovery semantics before claiming FT correction. Preserve current ideal-boundary mode for regression comparisons.
3. Use structured same-check/cross-check hook and flag-cancellation witnesses to guide interval placement and interaction swaps. Evaluate against random seeded mutations with equal budgets.
4. Add generating-basis transformations with phase-safe consistency checks and richer generic gadget families. Extend segmented gadgets only with a proof of correct check measurement.
5. Relax unnecessarily serial gadget dependencies and explore schedules while preserving observable semantics. Compare to current workload/dependency lower bounds.
6. Improve triple search with bounded pair tables and algebraic certification backends. Keep partial-search labels explicit. Add a Stim verification path when available, not as sole source of truth.
7. Only after correction semantics are established, add hardware-aware mapping/durations and controlled LER estimation.

Do not tune these improvements on held-out architectural answers. Freeze generic rules and benchmark configurations before held-out trials.
