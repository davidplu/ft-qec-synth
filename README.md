# FTQEC 0.1

A generic, reproducible research core for stabilizer syndrome-extraction architecture search. Pure Python, no runtime dependencies. Inputs are unsigned (+1), commuting Hermitian Pauli generators. CSS and non-CSS codes, dependent generators, arbitrary n and k are supported. Invalid commutation and hidden -I relations are rejected.

## Install and run

Python 3.10+:

```console
python -m pip install -e ".[dev]"
ftqec validate benchmarks/development/steane.json
ftqec generate benchmarks/development/steane.json --budget 12 --seed 7 -o results/generated.json
ftqec search benchmarks/development/steane.json --budget 1000 --seed 7 --max-weight 2 -o results/steane-search.json
ftqec frontier results/steane-search.json -o results/frontier.json
pytest
python experiments/run_development.py --budget 24
```

Without installation, set PYTHONPATH to the absolute `src` directory and use `python -m ftqec.cli` in place of `ftqec`. No network or simulator is needed for the core. Optional `pip install -e ".[verification]"` enables JSON-schema validation tests. To evaluate a circuit, save one `circuit` object from the generate output as `circuit.json`:

```console
ftqec evaluate circuit.json
ftqec faults circuit.json --max-weight 3 --max-combinations 2000000
ftqec search my_code.json --budget 100 --required-distance 3 --max-weight 2 --idles -o results/custom.json
```

Minimal input:

```json
{"name": "my code", "generators": ["XXXX", "ZZZZ"]}
```

For no generators, explicitly provide n. No target resources, schedules or flag hints belong in a code input. `benchmarks/held_out/` is reserved for later stabilizer-only inputs.

## Pipeline

Bit-packed symplectic algebra -> generic logical quotient basis -> seeded candidates -> extraction IR -> greedy scheduling -> resources -> precomputed linear fault signatures -> weight 1/2/3 hash searches -> explicit witnesses -> Pareto frontier -> beam mutations.

Candidates specify the input generating basis, support permutations, flag intervals, check order, syndrome slot assignment/budget and parallelism. SHA-256 IDs cover the complete candidate configuration. Search uses a nondominated finite beam; a deterministic lexicographic order only allocates the finite beam. The reported frontier uses Q, D, QD, two-qubit gates and certified distance lower bound, rather than a scalar score. Frontiers retain one reproducible representative per identical objective vector; raw records retain all alternatives. Frontiers retain one reproducible representative per identical objective vector; raw records retain all alternatives. Cross-code frontier aggregation keeps code input hashes separate.

Each check uses a |+> syndrome ancilla with controlled Pauli interactions. A Y interaction is SDG(data), CX(ancilla,data), S(data). Zero, one or two flag intervals are generated; the IR builder supports arbitrary configured interval counts. Paired CX(ancilla,flag) operations bracket each interval. Each flag is reset to |0>, measured in Z and reused only after its measurement epoch. The candidate intervals provide check segmentation into monitored intervals, not independently measured partial stabilizers.

`--budget` caps distinct evaluated candidates, not elapsed time. Duplicate pruning and a bounded mutation attempt count may yield fewer candidates. All stochastic choices use the provided seed. Runtime measurements are intentionally nondeterministic; architectures, metrics and bounds are reproducible.

## Read the result correctly

The default acceptance threshold is `--required-distance 2`: exclude all single-fault undetected logical failures under the documented model. Weight-two failures are retained with their exact/upper bounds and witnesses if the threshold is met. For a stricter screen, use `--required-distance 3 --max-weight 2`. This is a detection-distance criterion, **not a proof of fault-tolerant error correction**.

Stage A conservatively rejects resource dominance only against candidates fully screened through the requested weight; resources alone cannot justify discarding a potentially higher-distance candidate. B/C/D search weights 1/2/3. Once a witness is found, higher weights cannot improve its upper bound and are skipped. Every rejection is recorded. `stage_outcomes` also counts witnesses that meet the configured acceptance threshold. `frontier` contains accepted candidates; `exploratory_frontier` includes failed candidates for research feedback and must not be called a certified frontier.

Bounds are integer lower/upper bounds: excluding faults through t means d >= t+1 (d > t). A weight-t witness means d <= t. EXACT is emitted only when lower and upper agree. A work limit never certifies an unfinished layer. k=0 has no data logical failure; finite-order searches do not claim infinite distance.

See [the model](docs/FAULT_MODEL.md), [limitations](docs/V0_1_LIMITATIONS.md), [benchmark protocol](BENCHMARK_PROTOCOL.md), and [roadmap](docs/V0_2_ROADMAP.md). See [the development report](docs/DEVELOPMENT_REPORT.md). See [the development report](docs/DEVELOPMENT_REPORT.md). Saved demonstration and profile outputs are in `results/development/`.
