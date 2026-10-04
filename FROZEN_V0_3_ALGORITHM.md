# Frozen V0.3 algorithm before Development Suite 2 design

Algorithm commit: `50b926c793bbc78fa922c5eebf067678fec29504`. All 96 existing tests pass. The byte hashes of every runtime source and every previous V0.3 result are recorded in `results/development_v2/algorithm_freeze.json`. Neither may change during this experiment. Later experiment-script commits do not change the algorithm.

Strategies: RANDOM, RESOURCE_GUIDED, V0.2_CEGIS, V0.3_CEGIS, MIXED (one third random exploration). The V0.2 comparator is the previously documented contemporary matched comparator, not a replay of V0.2 raw results.

Generic mutations: flags (maximum four per check), interval splitting, hook-support reordering/reversal/swaps, cross-check ordering/serialization/separate ancillas; random local mutation and 1/12 noisy terminal-round toggle; resource reductions, flag removal, parallelism, ordering. The complete implementation is frozen by source hashes, including all mutation probabilities and tie breaking.

V0.3 uses diverse source classes, greedy uncovered expected class coverage divided by 1+added flag/round cost, run-local Laplace-smoothed operator success, and bounded guided queues. Pure terminal classes are unsupported. Witness transport is semantic and ambiguous transport is unresolved. Class equivalence retains physical mechanisms and individual effects; raw multiplicity and signature counts are separate. Counts are only comparable after complete enumeration; unknown is never zero.

Quality orders rigorous distance lower bounds first, then completed malignant counts. Resource Pareto dimensions are Q,D,QD,two-qubit gates. Protection reserves four of twelve beam slots for at most four evaluation ages; neutral compound depth is three. Source representatives four, option cap sixteen, initial population six. Randomness is a fresh Python Random(seed) per run; all arms share the same deterministic initial population. Cached duplicates consume evaluation slots. No learned state is transferred across runs.

Distance certification is unchanged bounded fault enumeration; spectra are heuristics, not certificates. Every distance-gain exclusion is independently checked. Product readout, ideal encoded input, logical index zero, three noisy rounds, no implicit idles. All initial hyperparameters:

```json
{
  "budget": 32,
  "seed": 0,
  "strategy": "v03",
  "target_dc": 3,
  "max_weight": 3,
  "max_combinations": 200000,
  "spectrum_work": 200000,
  "beam_width": 12,
  "initial_population": 6,
  "idles": false,
  "equivalence": "structural",
  "protect_progress": true,
  "dominant_order": true,
  "coverage_priority": true,
  "protected_slots": 4,
  "protection_age": 4,
  "compound_depth": 3,
  "representatives": 4,
  "option_limit": 16
}
```

The default evaluation budget is 32. Development Suite 2 may prospectively use an enlarged matched evaluation budget, more seeds, and task-specific targets, recorded before comparison; no beam, scoring, mutation, equivalence or coverage tuning is permitted. Certification and spectrum caps stay 200000, maximum weight three. Higher targets cannot be claimed from incomplete tiers. Frozen ablations are raw/signature equivalence, no protection, arbitrary source ordering, and no coverage priority.

Any discovered bug will be documented separately without silently altering the frozen source. New code generation, screening, auditing and reporting live outside `src/ftqec`. New selected codes are development forever. Held-out inputs and optimized architectures are not read.
