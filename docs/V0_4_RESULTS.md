# V0.4: resource Pareto synthesis under certified distance constraints

**NOT_READY_FOR_HELD_OUT.** Compression works, but the bounded primary search
does not yet reliably return valid frontiers across the required development
parents. Its native work cap also hides certifiable cat circuits. Higher target
certification remains unsupported. No held-out code or final architecture
package was run or imported, and no readiness algorithm freeze was created.

## Objective and implementation

Return Pareto implementations minimizing **Q, D, QD and two-qubit gate count**,
subject to certified circuit distance at least the user's target. Distance above
the target gives no preference over a cheaper valid implementation. Independent
metric minima can belong to different architectures; they are not combined
into an imaginary best circuit or universal practicality score.

V0.4 lives in `ftqec.resource_synthesis`. The 45 V0.3 source files remain
byte-identical. INVALID candidates have independently replayed witnesses below
target; VALID candidates have completed exclusions through target minus one;
UNKNOWN means the bounds straddle the target. Invalid ideal detector parities
are separately marked INVALID_STRUCTURE. The search maintains bounded valid
and near-valid resource archives, complete ancestry, run-local repair-cost and
compression statistics, and distance-conditioned frontiers for every achieved
certification tier. Final output reconstructs the full observed frontier even
when the exploration archive was truncated.

Invalid candidates receive generic witness/class-guided repairs. Valid parents
receive resource-attributed compression proposals, prioritized by predicted QD
savings; failed proposals retain their invalid region and can be repaired again.
A failed compression never replaces a valid incumbent. The Pareto output still
retains Q/depth/gate tradeoffs regardless of the proposal ordering heuristic.

Supported physical edits remove flags, merge flag intervals, share flag and
syndrome ancillas, omit redundant measured epochs and the extra terminal round,
remove individual flag interactions and resets, and increase parallelism or
simplify interaction order. Merging flag records and deleting terminal detector
channels are also attempted; these classical edits have **zero direct quantum
resource savings**. The fourteen requested mutation descriptions include aliases:
independent-interval reduction uses flag removal; sequence shortening uses epoch
removal; serialization reduction uses parallelism; duplicated information
reduction uses interval/record merging. Each generator retains at least one
physical measured epoch. No mutation is assumed to preserve fault tolerance.

Every edit gets a fresh deterministic dependency/physical-qubit ASAP schedule.
Q footprints and depth spans overlap and are not additive component costs;
gate/measurement/reset totals are additive. Saved attribution reports each
check epoch, terminal readout, flag operations, shared ancillas, reuse dependency
edges and extra rounds. This is schedule reoptimization within the supported
dependency graph, not globally optimal scheduling or hardware routing.

Positive signed row products provide bounded stabilizer-basis search. Negative
products are rejected because the input format represents +1 Hermitian rows.
Both binary span and signed group membership are checked; the original physical
logical observable and readout axes remain fixed. Inventories record generator
weights, overlaps, qubit degrees and predicted extraction resource minima.

The family plugin interface preserves interval-flag gadgets and adds a generic
**verified cat-state candidate family**: GHZ controls couple individually to
data, noisy Z0Zj verification measurements become detectors, and X-parity cat
readout supplies the syndrome. There is no postselection or ideal cat factory.
The topology and fault propagation differ from a single syndrome control.
The choice was documented before implementation in [the protocol](V0_4_PROTOCOL.md),
motivated by [Shor](https://arxiv.org/abs/quant-ph/9605011) and
[Prabhu and Reichardt](https://quantum-journal.org/papers/q-2023-10-24-1154/).
Those papers do not supply certificates for these generated circuits.

## Preservation and prospective experiment

The baseline was clean at `fd29e51d17bfd1e8855fefe257bf22b132525dba`;
99 tests passed before source changes. All **1,332** preserved historical
source/results hashes still match, including V0.1, V0.2, V0.3 and Development
Suite 2. Development occurred on `development/v0.4`.
The original record covers 1,318 files; the fourteen root/development V0.1
results additionally match the immutable pre-V0.4 archive exactly.
Git had normalized line endings in 120 V0.2 JSON/JSONL files despite their
preserved Windows bytes. A storage-only attribute/restaging correction retains
the existing bytes across checkouts; no historical file was rewritten and no
scientific value changed. The published V0.2 tag is untouched.

The experimental algorithm was committed before comparisons at
`e0ef5c14e2992ab2a4885ea5d22e96756c732454`. Its source, inputs, seeds,
settings and prospective protocol are recorded in
`results/v0.4/experiment_freeze.json`. Later diagnostic extensions refine
minimality labels and accelerate audits without changing that search.

The primary comparison uses six Development Suite 2 tasks, **target=3**, three
mandatory time blocks, the same six generic initial candidates per task/seed,
seeds **10,11,12**, and **48 evaluation slots** per run. Algorithms: unchanged
V0.3, V0.4 repair/compression, resource and random; additional basis-off and
family-off ablations. Native work caps are 200,000. V0.3 keeps its existing
weight-three screen; V0.4 screens through target minus one. Both report the
same target constraint and independently audit every reported final frontier.
Duplicates, unsuccessful mutations and invalid ideal circuits consume slots.

The complete saved experiment contains **144 runs, 6,912 slots**: 108 primary,
18 bare-start, 12 valid overprotected-start, and six supplemental prefix-start
runs. The initial full-interval duplicate-flag affine starts failed native target
certification and remain in the calibration record. They were not replaced in
the prespecified experiment. The separate prefix supplement was specified
before its comparisons; six larger prefix starts were native UNKNOWN and three
Steane starts were native VALID. Calibration, failures and caps are all saved.

The chosen physical memory model has ideal encoded input, noisy extraction,
physical product readout, and **no idle faults**. Each task protects **one chosen
logical observable**, including k>1 codes. Omitting measured epochs retains the
three time blocks but removes gates/noise locations; it does not certify
realistic storage protection or all logical observables. These limitations also
apply to interpreting large compression savings.

## Primary validity and resource comparison

| Task | V0.3 | V0.4 | Resource | Random |
|---|---:|---:|---:|---:|
| affine15_k1-X | 0/3 | 0/3 | 0/3 | 0/3 |
| steane14_sum-Z | 3/3 | 2/3 | 1/3 | 2/3 |
| steane7-X | 3/3 | 3/3 | 0/3 | 2/3 |
| simplex15_k7-X | 0/3 | 0/3 | 0/3 | 0/3 |
| steane7_mixed-X | 3/3 | 3/3 | 0/3 | 1/3 |
| simplex15_k7-Z | 1/3 | 1/3 | 0/3 | 0/3 |
| Total | **10/18** | **9/18** | **1/18** | **5/18** |

These are frozen **native-returned certification endpoints**, not claims that
every unsuccessful run lacks a physically valid architecture. The CSS/mixed
Steane tasks and the direct sum are related controls, not three independent
parent constructions. The primary reliable tasks collapse to one Steane parent.

Ratios below compare independent per-metric minima only on jointly valid paired
runs. Missing validity stays missing; unsuccessful runs do not receive cheap
resource values. Denominators are small and selected by joint success. These
are descriptive development observations, not general-superiority claims.

| V0.4 / baseline | Joint-valid pairs | Q | D | QD | 2Q |
|---|---:|---:|---:|---:|---:|
| V0.3 | 8 | 0.857 | 1.239 | 1.034 | 0.832 |
| Resource | 1 | 0.950 | 0.544 | 0.414 | 0.604 |
| Random | 5 | 0.923 | 2.481 | 2.031 | 0.892 |

Entries are median paired ratios. V0.4 covers the entire resource baseline
frontier in its single jointly successful pair, but covers the random frontier
in only **one of five** jointly valid pairs. Against V0.3 it covers two of eight;
one V0.3 frontier covers V0.4; the remaining pairs contain tradeoffs. V0.4 has
one validity win and two losses against V0.3, eight wins against resource and
four against random. More target returns do not establish better resource cost.

## Compression from valid starts and bidirectional trajectories

The two eligible overprotected parent codes each retain target validity in all
three seeds. Each row below reports **independent minima**, potentially from
different Pareto points.

| Start / variant | Q | D | QD | 2Q |
|---|---:|---:|---:|---:|
| Steane7 repair-only | 25 | 386 | 9,650 | 192 |
| Steane7 repair/compression | 12 | 46 | 736 | 86 |
| Simplex15 repair-only | 39 | 642 | 25,038 | 384 |
| Simplex15 repair/compression | 27 | 66 | 1,782 | 216 |

Across these six matched valid-start pairs, mean absolute savings are **12.5
qubits, 458 depth units, 16,085 QD and 137 two-qubit gates**. Median paired
reductions are **41.4% Q, 88.9% D, 92.6% QD and 49.5% 2Q**. The original
overprotected starts and outputs are identical across seeds within each parent;
they demonstrate reproducibility, not six independent circuit constructions.

The randomized-prefix Steane supplement also preserves target in 3/3 pairs:
median QD ratio 0.0374, mean Q saving 24 and mean gate saving 204.7. Affine and
simplex prefix starts were excluded as native UNKNOWN, not presumed invalid.

Bare starts are initially broken. Both strategies reach target on Steane in
3/3 seeds and fail to return certified target on affine/simplex in 0/3 each.
On Steane, one-way repair gives **(Q,D,QD,2Q)=(12,578,6936,234)**;
repair/compression gives **(12,193,2316,78)**. Compression saves 385 depth,
4,620 QD and 156 two-qubit gates, with no Q saving. The ancestry includes bare
broken extraction, switching to protected cat extraction, and removing redundant
epochs. This is direct evidence of a functioning bidirectional mechanism on
that development case, not reliable improvement across all parents.

An actual Steane overprotected frontier retains the tradeoff between a cat
implementation **(12,482,5784,195)** and an interval-flag implementation
**(16,46,736,86)**. Smaller Q and smaller depth/QD/gate count are different points.
An extra terminal noisy round, duplicated flags and unnecessary serialization
can be removed in certified surrounding architectures.

Successful removal example: from the compressed bare Steane finalist, a reset
removal remains certified with **(12,192,2304,78)**, proving the returned point
still has a cheaper neighbor. Failure example: removing its cat verification
gives **(11,121,1331,42)** but an independently replayed **weight-two logical
witness** violates target three. Deleting half a paired flag interaction can
instead make an ideal detector intrinsically random; such candidates are
INVALID_STRUCTURE, not alleged distance-two evidence.

## Local necessity, basis and family evidence

All **50** audited V0.4/ablation final Pareto nodes remain
**NOT_LOCALLY_PROTECTION_MINIMAL**: a supported single edit can still lower
some resource while preserving target. Local audits test all supported single
removals, not pairs or global architecture optimality. Removing a feature can
produce a useful Pareto tradeoff without dominating the parent. Conservative
labels disallow a minimality claim whenever a cheaper valid or unresolved
neighbor exists.

The completed removal audits contain **5,899 feature tests**. Most frequent
removable categories are reset-cycle reductions (**1,720**) and redundant
measured epochs (**818**). Flags, interval merging and syndrome/flag reuse are
also removable in many surrounding circuits. Highest-count physically proven
necessary categories are terminal detector channels (**157**), flags (**58**),
merged flag records (**31**) and cat verification (**23**). Counts include
repeated/equivalent architectures and uneven operator opportunity; they are not
universal necessity rates. The **1,604** half-flag interaction failures and
**772** reset failures classified EMPIRICALLY_NECESSARY are ideal-structure
failures and remain separate from malignant witness proofs.

Run-local statistics track representative-witness outcomes, certified gains and
resource deltas for proposal ordering. A separate diagnostic reconstructs and
tests complete target classes using independently replayed child singleton
effects: **1,717** repair outcomes. Partial source classes and removed/ambiguous
fault locations never receive automatic elimination credit; a mapped surviving
realization can still disprove elimination, otherwise the result is UNKNOWN. Full-class
elimination is not inferred from eliminating a representative. Detailed operator
probabilities and conditional valid compression savings are machine-readable.

Basis-off reaches 8/18 targets versus 9/18 full V0.4. On eight joint-valid pairs,
the median full/basis-off QD ratio is **1.142**, with no median Q improvement.
Five basis-off frontiers cover full V0.4, two pairs are equal and one contains
tradeoffs. Basis search adds the simplex-Z seed-11 target, but a material general
resource-frontier benefit is **not established**; it often spends budget badly.

Family-off reaches **3/18**, versus **9/18** with the cat family. Cat extraction
supplies valid low-Q points on Steane and its mixed control that family-off fails
to return in several seeds. On three jointly valid pairs, median QD ratio is one;
two frontiers are equal and one trades resources. The extra family improves
reachability and some Q frontiers, with substantial depth overhead in other
cases. This is a finite development observation, not a literature-derived FT
guarantee or universal family advantage.

## Returned target-three frontiers

Pooled across three primary seeds; metrics are independent minima. Full points
and every achieved distance tier are available in the JSON outputs.

| Task | min Q | min D | min QD | min 2Q |
|---|---:|---:|---:|---:|
| affine15_k1-X | missing | missing | missing | missing |
| steane14_sum-Z | 19 | 64 | 1,748 | 134 |
| steane7-X | 12 | 226 | 2,712 | 91 |
| simplex15_k7-X | missing | missing | missing | missing |
| steane7_mixed-X | 12 | 84 | 1,512 | 96 |
| simplex15_k7-Z | 28 | 118 | 3,304 | 222 |

For steane14_sum-Z the actual points are **(29,64,1856,144)** and
**(19,92,1748,134)**. For the mixed Steane control the actual points are
**(12,330,3960,130)** and **(18,84,1512,96)**. The supplied mixed basis/control
is its own frozen input sector; V0.4 basis mutations preserve that signed sector.
The smaller overprotected-start frontiers above are a **separate experiment**
and are not substituted into the primary matched-start comparison.

## Certification, censoring, runtime and readiness

All **113 tests pass**. Persisted-data verification checks all 144 runs, matched
initial populations and budgets, schemas, circuit hashes and ideal parities;
it reconstructs **4,414 unique architecture/model combinations**, independently
replays **3,869** saved witnesses and checks **83** final frontier exclusion
certificates. These include baselines and repeated appearances; counts do not
mean 83 independent experiments.

Safe delta screening reuses suffix transfer maps only when physical suffix
gates/qubits/records and output coordinates/maps are identical. Changed output
channels or ancilla allocation disable reuse. New fault locations are enumerated
afresh; tests compare delta results to full suffix and independent forward
propagation. Final exclusion uses separately implemented physical singleton
replay and detector joins. Necessity audits omit unused diagnostic spectrum
construction and cache only identical design/memory/target/cap certificates;
the native bounds and independent exclusions remain unchanged.

There are **161 native UNKNOWN candidate records** across saved V0.4 runs.
A separate bounded audit selects up to four resource extrema among UNKNOWN
primary records and all six UNKNOWN prefix starts: **30 references, 25 unique
circuits**, all independently exclude faults through weight two. Twelve V0.4
primary runs contain such audited candidates; union with native-returned target
runs shows a target-certifiable circuit in **18/18** primary V0.4 runs. This is
**post-experiment diagnostic coverage**, not native algorithm success or a
complete upgraded frontier. The expensive cat witnesses of validity remain
uncompressed in several capped runs. The frozen target endpoint stays **9/18**.
Both observations are needed: physical target feasibility is better than the
native return rate, while the current search/certifier interface is inadequate.

Primary V0.4 median search runtime is **20.06 seconds**, maximum **44.00**;
overprotected compression median is 36.06 seconds and the prefix supplement
58.26 seconds. Summed search time across all runs is **2,565.71 seconds**;
driver time is 2,579.33 seconds. Several groups ran concurrently, so these are
contention-affected elapsed times, not dedicated-machine CPU benchmarks.
Independent saved-data verification took 90.37 seconds. Runtime is affordable
for these n=7/14/15, target-three experiments; targets above four lack a supported
independent certifier here, and distance-seven/nine feasibility is unestablished.

The unchanged prospective gate passes tests, material valid-start compression
across two parents/seeds, independent final audits, meaningful tradeoffs, low-tier
runtime and held-out isolation. It **fails primary native target reliability
across three parents and justified higher-tier certification scaling**. Local
minimality is also unfinished. Thus **NOT_READY_FOR_HELD_OUT**. No thresholds
were relaxed after observing results and no `V0_4_ALGORITHM_FREEZE.md` exists.

All gate, reset, measurement and Clifford durations are one abstract time unit;
connectivity is unconstrained. Reuse dependencies and serialized cat preparation
explain measured depth, but optimal schedules, alternative cat factories,
mutation-budget allocation and the cost gap to human circuits are not resolved.
The hardware meaning of the savings, idle-inclusive protection, full logical
memory and higher-order certification remain unexplained. No high-statistics
LER, corpus scanning, code discovery, routing, neural model or GUI was added.

Future held-out comparisons must use the already frozen target/model-matched
human-frontier minima Q,D,QD,2Q ratios and pointwise dominance in
[V0_4_PROTOCOL.md](V0_4_PROTOCOL.md). Its exact descriptive ratio intervals were
fixed before this experiment. No human resource values were read or used.

## Explicit answers to the eighteen questions

1. **Reliably reach target?** Not as a native returned result across parents:
   9/18. Separate physical post-audits find a certifiable candidate in all 18;
   capped candidates still do not enter the returned valid frontier.
2. **Remove unnecessary protection once valid?** Yes: all six prespecified
   eligible valid-start pairs retain target while reducing resources.
3. **Q savings?** Mean 12.5; median relative reduction 41.4% in those six pairs.
4. **Depth savings?** Mean 458 units; median reduction 88.9%.
5. **QD savings?** Mean 16,085; median reduction 92.6%.
6. **Two-qubit gate savings?** Mean 137; median reduction 49.5%.
7. **Beat repair-only?** Yes in the eligible valid-start compression test;
   bare Steane also saves about two-thirds of depth/QD/gates. Not across all
   broken-start parents.
8. **Beat resource-guided at matched distance?** In the one jointly valid pair,
   yes, including frontier coverage; general superiority is unsupported.
9. **Beat random at matched distance?** Not generally: median QD is 2.031 times
   random on five joint-valid pairs, despite more native target returns.
10. **Locally protection-minimal?** No: all 50 audited final nodes have a
    cheaper supported valid single-edit neighbor.
11. **Most frequently removable?** Reset cycles and redundant measured epochs;
    conditional, opportunity-weighted counts, not universal necessity facts.
12. **Most frequently necessary?** Terminal detector channels, flags, merged
    flag channels and cat verification by physically replayed failure witnesses.
13. **Material basis-frontier benefit?** Not established; one extra target but
    worse median QD than basis-off on joint-success pairs.
14. **New family improve a frontier?** Yes: cat-derived valid low-Q Steane
    points and six additional target returns versus family-off; other cases pay
    depth cost.
15. **Bidirectional better than one-way repair?** Yes for the controlled valid
    starts and bare Steane trajectory; not yet reliably across all parents.
16. **Best distance-conditioned frontiers?** The primary target-three table
    and actual points above; all tiers and separate-start frontiers are saved.
17. **Unexplained cost?** Residual removable protection, cat serialization,
    basis/proposal budget allocation, native cap censoring and hardware costs.
    No comparison to unseen human resource numbers was attempted.
18. **Practical held-out-scale runtime?** Low-order development runs are
    affordable; higher-distance held-out certification remains unestablished.

## Reproduce and inspect

Install `pip install -e ".[dev]"`. The public V0.4 CLI is `ftqec`; historical
commands are `ftqec-v03`. Package metadata and the new API are version 0.4.0;
the immutable historical `ftqec.__version__` constant remains 0.3.0.

Use `python experiments/run_v04.py verify` to verify the frozen inputs;
`primary` and `secondary` resume missing runs without replacing completed raw
files. `python experiments/v04_valid_starts.py` reproduces the separate prefix
supplement. `audit_v04_fast.py`, `audit_v04_classes.py`,
`audit_v04_censoring.py`, `v04_operator_summary.py`, `verify_v04.py` and
`report_v04.py` reconstruct diagnostics and summaries. The guarded `freeze`
command refuses to overwrite the existing experiment freeze.

Data: `results/v0.4/raw/*.json.gz`, `minimality/*.json.gz`,
`preservation.json`, `v01_preservation.json`, `experiment_freeze.json`, `secondary_starts.json`,
`prefix_starts.json`, `aggregate.json`, `pareto_frontiers.json`,
`distance_conditioned_frontiers.json`, `design_inventory.json`,
`operator_statistics.json`, `whole_class_repair_audit.json`,
`censoring_audit.json`, `verification.json`, `final_tests.xml/json`.
The isolated built-wheel CLI smoke also passed. Runtime requires only the
standard library; tests/schema validation use the declared dev dependencies.

Machine-readable ancestry: `results/v0.4/trajectories.json`.
Vector figures: `trajectories.svg` (evaluation order) and
`distance_tier_trajectories.svg` (certified distance tier). Green means native
certified valid; red means broken/unknown. Plotted tiers are lower bounds, not
invented exact distances. Plot-selected examples are explanatory, not endpoints.
