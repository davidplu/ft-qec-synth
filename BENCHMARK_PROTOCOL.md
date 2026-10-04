# Research isolation and benchmark protocol

This synthesizer is developed without access to previously hand-optimized architectures for held-out research codes. No held-out architectural answers were imported or consulted. No internet search for precomputed optimal architectures is part of this workflow.

The software contains no code-specific flag placements, schedules, winning architectures or expected held-out resource counts. Development fixtures comprise repetition, perfect-five, Steane, a four-qubit CSS example and a four-qubit non-CSS example. Their stabilizer definitions validate generality; small-code distance expectations occur only in algebra tests, never in architecture synthesis. The 23/25/31/44 research architectures are not development targets.

Held-out inputs must contain only name, n if needed and unsigned stabilizer generators. Freeze source version, fault model, seed set, evaluation budget, required distance, idle policy and work limits before evaluation. Keep held-out outputs separate from development outputs. Do not tune generic search rules using held-out resource targets or compare scores from differing boundary/fault models as equivalent.

Report every rejected and accepted candidate, exhausted work limits, lower/upper bounds, witness and runtime. Compare only common physical-fault and boundary models. A frontier is bounded-search output, never a global optimum. Failed or empty-frontier experiments remain part of the benchmark record.

## V0.2 frozen development pilot

Only css4, noncss4, perfect5 and Steane development inputs are used. R=3, both X/Z memory at logical index 0, ideal encoded input, physical product readout, idles disabled, maximum weight 3, 200000 fault-search work entries, seeds 0/1/2, six shared initial candidates and 24 proposal/evaluation slots per run are frozen for all four ablations. Duplicate proposals consume slots and use the same cache policy. Target d_c=3 conditions resource frontiers; unattainable or unreached targets remain explicit empty frontiers. Optional idle/input-noise semantics are tested but not mixed into this pilot.

This is a small pilot, not evidence of statistical significance. Strongest-distance comparisons, target reach, time and quality/resource improvements are separate from eliminating an individual source witness. Do not reinterpret a local repair as a global search advantage. No held-out code may be run merely because the implementation passes tests.
