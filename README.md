# FTQEC 0.3

Repeated noisy syndrome-extraction memory experiments and counterexample-guided architecture search, extending the V0.1 research core. No held-out architectural answers are included. Runtime uses only the Python standard library; the full development suite declares pytest and jsonschema.

V0.3 adds complete low-weight malignant spectra, structural fault classes, a
bounded progress archive, diverse class-targeted repairs, estimated set-cover
ordering, ancestry and independent exhaustive audits of distance gains. The
published `v0.2.0` tag preserves the pre-V0.3 baseline and its results.

Use `ftqec search benchmarks/development/css4.json --search-version 0.3 --strategy v03 --budget 32`
for the new algorithm. `--equivalence raw|signature|structural` selects its
malignant objective. `ftqec spectrum circuit.json --max-weight 3` evaluates a
saved circuit's bounded spectrum. Legacy search remains available with
`--search-version 0.2`; V0.2 raw files are never overwritten by V0.3 experiments.

The prospective protocol is [V0_3_HYPOTHESIS.md](docs/V0_3_HYPOTHESIS.md), and the
exact mechanism definition is [MALIGNANT_CLASSES.md](docs/MALIGNANT_CLASSES.md).
`python experiments/run_v03.py` runs the frozen development experiment into
`results/v0.3`; `python experiments/report_v03.py` validates and reports it.
Raw JSON is losslessly compressed with gzip and validates against
`docs/schemas/result-v0.3.schema.json` after decompression.

## Install and test

Python 3.10+, from this repository:

```console
python -m venv .venv
.venv\Scripts\activate
pip install -e ".[dev]"
pytest
python experiments/run_tests.py --results-dir results/v0.3
```

On POSIX activate with `source .venv/bin/activate`. Editable installation is the normal workflow; no manual PYTHONPATH is required. The automated verification command saves JUnit XML and a JSON summary. Missing test dependencies fail explicitly instead of skipping.

## End-to-end example

```console
ftqec validate benchmarks/development/steane.json
ftqec memory benchmarks/development/steane.json --rounds 3 --basis Z -o results/memory.json
ftqec evaluate results/memory.json
ftqec faults results/memory.json --max-weight 3 -o results/faults.json
ftqec verify results/memory.json --witness results/faults.json
ftqec decode results/memory.json --max-weight 1
ftqec search benchmarks/development/steane.json --budget 1000 --seed 7 --rounds 3 --basis Z --target-dc 3 --strategy cegis -o results/search.json
ftqec frontier results/search.json -o results/frontier.json
```

`memory` defaults to the generic bare candidate. Supply `--candidate candidate.json` to build a particular candidate object saved from a search record. `generate` retains the V0.1 bounded candidate/single-round export. To run its legacy evaluation explicitly, use `search --model ideal-boundary`; these outputs retain the 0.1 result schema and are not mixed with repeated-memory results. Repeated memory is the default search model. Frontiers are grouped by code, model, memory basis/index/rounds/input policy, idle policy and target threshold.

Input is only a stabilizer definition:

```json
{"name": "custom", "generators": ["XXXX", "ZZZZ"]}
```

Signed Pauli inputs are not supported; strings specify +1 Hermitian generators. Empty generator sets require n. Algebra supports CSS/non-CSS, arbitrary n/k and dependent generators, rejecting noncommuting or -I-implying input. Logical representatives are generic, not optimized for weight. k>1 memory experiments select `--logical-index` and test one X/Z observable per run.

## What changed from V0.1

The existing algebra, gadget, candidate, scheduler, resource and bounded fault-search modules remain. V0.2 adds round/operation metadata, temporal detectors, physical final readout, separate decoder metrics, independent witness replay, deterministic counterexample analysis, provenance-labelled targeted repairs and matched search ablations. Signature construction now uses backward packed transfer maps, checked against forward propagation and independent actual-state tests. Public serialization returns JSON-native arrays, and source-layout tests run after the declared editable install.

A default round means one complete measurement of all supplied checks. R=3 is a fixed development convention, not implicitly the code distance. The input encoded logical state is ideal; optional `--noisy-input` adds local output-preparation faults. Ancilla preparation/reset, gates and measurement are noisy; `--idles` enables storage faults. Final detectors close the full stabilizer subgroup compatible with the physical product readout, including signed products of supplied generators. Non-CSS cases can consequently have a distance-one readout ceiling. Read [the exact fault model](docs/FAULT_MODEL.md) before interpreting any bound.

Distance is decoder-independent: zero temporal/flag detectors plus a flipped final logical observable. Decoder failures, including nonzero-syndrome collisions, are separate results. EXACT is emitted only when lower/upper bounds meet; partial search is never certified. Weights 1–3 use hashing/meet-in-the-middle; weights 4–6 are supported for small tractable cases with explicit work limits. No LER or global optimality claim is made.

## Controlled development experiment

```console
python experiments/run_v02.py --budget 24 --seeds 0 1 2 --rounds 3
```

Four development codes, X/Z memory, three seeds and four strategies (random/resource/CEGIS/mixed) use identical populations, evaluation slots and mutation counts. Duplicate proposals consume slots under every strategy; raw records retain cache status and all provenance. Runs, paired comparisons, repairs and profiles are saved in `results/v0.2/`. The current pilot does not establish a CEGIS search advantage.

See [CEGIS and repair definitions](docs/CEGIS.md), [V0.2 results and readiness](docs/V0_2_RESULTS.md), [limitations](docs/V0_2_LIMITATIONS.md) and [research isolation](BENCHMARK_PROTOCOL.md). JSON schemas are under `docs/schemas/`; use `result-v0.2.schema.json` for repeated-memory results and `result.schema.json` for legacy V0.1 outputs.
