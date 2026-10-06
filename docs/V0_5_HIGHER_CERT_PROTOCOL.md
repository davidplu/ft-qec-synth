# Prospective higher-distance SAT verification supplement

The initial Shor 5x5 and 7x7 three-round attempts stopped at native lower bound 3
with terminal-readout upper bounds 5 and 7. Their independent location trellises
hit state/work caps. Repetition-channel results do not satisfy readiness.

Before further solver runs, define this separate supplement. OR-Tools 9.15.6755
is installed as an optional project-local verification dependency. Use independently
forward-replayed physical singleton effects, one Boolean per physical fault
variant, at-most-one selection per physical location, zero detector XORs, at
least one nonzero logical XOR, and sum of selected variants <= target-1.
INFEASIBLE gives a lower bound; FEASIBLE/OPTIMAL supplies a physically replayed
upper witness; UNKNOWN supplies neither. Save model files and response metadata.
This is separate from the type-deduplicated meet-in-the-middle engine.

Fixed limits: one worker, seed 0, 60 seconds and 30 deterministic solver-time
units per check. Check the permanently development-only Shor 4x4, 5x5 and 7x7
constructions, rounds 1 and 3, selected Z observable, existing verified-cat family.
Also run native type joins with 1048576 work units and 250000 table entries.
No added family, hand repairs, held-out code or held-out architecture is used.
For sizes 5 and 7, run both weight target-1 and target to cross-check the threshold
and witness; a timeout never becomes an infeasibility claim. Native and SAT
results stay separately attributed. Exported models require solver reruns and
are not portable independently checked UNSAT proof traces.

Readiness retains every original gate. A SAT success alone does not waive native
scaling, compression completeness or practical held-out runtime requirements.
References: [official CP-SAT status definitions](https://developers.google.com/optimization/cp/cp_solver)
and [official Boolean constraint implementation](https://github.com/google/or-tools/blob/stable/ortools/sat/python/cp_model.py).
