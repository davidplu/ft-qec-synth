# V0.1 limitations

- Architecture space is bounded and incomplete. Generating basis is recorded and validated but not mutated. Generic orderings, intervals, allocations and parallelism are explored; no optimum is claimed.
- One-round ideal-boundary detection-distance screening is not full FT correction certification. In particular, equal nonzero-syndrome/flag faults with different logical cosets can be correction-incompatible. There is no decoder or recovery circuit.
- The gadget library is limited to controlled-P ancilla measurements and paired flag intervals. Segmentation means monitoring interaction intervals; partial stabilizer measurement and cat-state gadgets are absent. No code-specific design is imported.
- Scheduling is heuristic with unit durations and deliberately serial gadget dependencies. The lower bound need not be tight.
- Searches cover at most weight three, require distinct locations and have explicit work limits. No exact high-distance certification, probabilistic noise model or high-statistics LER is implemented.
- Signature construction resimulates each single fault; it is exact but the main current bottleneck. Cache reuse is within each candidate's staged search. No persistent signature cache or multiprocessing.
- Pareto frontiers are finite evaluated sets. Acceptance thresholds and the boundary/fault model must accompany comparisons. Beam allocation can miss promising architectures; failed exploratory parents are permitted only when there is no accepted beam.
- Hardware interface checks connectivity and metadata only. No router, mapping optimizer or duration-aware schedule is supplied.
- Stim is optional future work; independent dense matrix checks cover supported unitary Clifford propagation now.
- Reproducibility records include source commit if git is available, otherwise null. Keep the source archive with results when no commit exists.

Held-out evaluation is ready for stabilizer validation, generic candidate generation, scheduling/resource accounting, this documented fault model, low-order witnesses/bounds and machine-readable finite Pareto comparisons. It is not ready to compare full FT correction performance against hand-designed circuits without matching boundary, recovery and noise models.
