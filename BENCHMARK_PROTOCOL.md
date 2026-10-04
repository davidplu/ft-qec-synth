# Research isolation and benchmark protocol

This synthesizer is developed without access to previously hand-optimized architectures for held-out research codes. No held-out architectural answers were imported or consulted. No internet search for precomputed optimal architectures is part of this workflow.

The software contains no code-specific flag placements, schedules, winning architectures or expected held-out resource counts. Development fixtures comprise repetition, perfect-five, Steane, a four-qubit CSS example and a four-qubit non-CSS example. Their stabilizer definitions validate generality; small-code distance expectations occur only in algebra tests, never in architecture synthesis. The 23/25/31/44 research architectures are not development targets.

Held-out inputs must contain only name, n if needed and unsigned stabilizer generators. Freeze source version, fault model, seed set, evaluation budget, required distance, idle policy and work limits before evaluation. Keep held-out outputs separate from development outputs. Do not tune generic search rules using held-out resource targets or compare scores from differing boundary/fault models as equivalent.

Report every rejected and accepted candidate, exhausted work limits, lower/upper bounds, witness and runtime. Compare only common physical-fault and boundary models. A frontier is bounded-search output, never a global optimum. Failed or empty-frontier experiments remain part of the benchmark record.
