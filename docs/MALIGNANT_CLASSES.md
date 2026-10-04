# Exact low-weight malignant mechanisms

A malignant realization has distinct physical fault locations, zero detector
parity and a nonzero chosen memory logical effect. Raw multiplicity counts every
unordered physical fault/Pauli realization separately.

Structural equivalence is equality of the canonical MalignantFaultClass key:
weight, total detector parity, logical effect, sorted multiset of fault mechanism
tuples, union of multi-data propagated hook supports, and total flag parity.
Each mechanism retains absolute round, check, gate, fault kind, operation role,
flag interval, interaction position, data targets, multi-data hook support, named
individual triggered flag records, named detector-row effects, individual logical
effect and full propagated final-data Pauli. Detector rows are named by their
measurement records, so adding unrelated rows does not renumber existing effects.
Ancilla physical numbering, Pauli fault label, operation list index and ordering
of the faults are omitted only when every retained mechanism effect agrees.
Different checks, rounds, data supports or observable effects are never identified
by a symmetry assumption. This is intentionally conservative: it does not claim
a maximal equivalence relation or count mutually exclusive realizations as one
probabilistic event. Many classes can remain singleton classes.

Signature equivalence retains only weight, total detector parity and logical
effect. Because malignancy requires zero parity, it can be very coarse (one class
per nonzero logical effect/weight). Raw equivalence identifies no realizations.
All three counts are measured by the same enumeration and tested as objectives.

Enumeration uses matching detector buckets for pairs and pair/single joins for
triples, requiring increasing indices and distinct locations. It scans the entire
first malignant layer, rather than stopping at the first witness. Lower empty
layers are complete; higher layers are explicitly not searched. A work cap makes
the interrupted layer's counts null: observed partial counts and multiplicities
are diagnostics only. Unknown never means zero. The scalar raw/class/signature
count is selected by the ablation; no weighted resource/fault scalar is used.

Quality prioritizes rigorous distance lower bound, then complete malignant count
at that bound, then subsequent complete counts. A Pareto archive retains that
quality/resource tradeoff over Q, D, QD and two-qubit gates. At most four recently
improving equal-distance candidates are protected within a beam of 12 for four
evaluation slots. At most three neutral progress steps form a compound segment;
only a count decrease renews progress protection. A distance gain starts a new
segment. Duplicate slots and every beam decision are recorded. The full evaluated
record history is retained for audit, but proposal selection is bounded.

Dominant representative selection first favors low weight and repairability,
then additional check/round/hook/logical/failure diversity, multiplicity,
within-run recurrence and hook size. Four classes generate at most 16 options.
Identical proposed child architectures merge their source-class coverage sets.
Greedy uncovered expected coverage divided by one plus added flag/round units
orders those options; run-local Laplace-smoothed operator/failure successes break
ties. This is an expectation heuristic, not observed elimination. Actual resource
deltas are recorded after evaluation. No uncharged fault evaluation is used to
rank options. No code-specific circuit solution is stored.

Repair categories use net complete structural-count changes: REGRESSION takes
precedence, negative change is CLASS_ELIMINATION or MULTI_CLASS_IMPROVEMENT,
zero/unknown change plus exact source elimination is SOURCE_ONLY, otherwise
NEUTRAL. Complete layer deltas, disappeared/new mechanism keys and source
transport outcomes are separate. A disappeared key alone does not prove transport
elimination: a mutation can transform descriptors. Every raw realization of the
targeted parent class is transported by the independent replay path; any ambiguous
address yields unresolved rather than credit. All transported parent members being
eliminated still does not mean no new child alternatives exist. Net class counts
and new keys expose that distinction.

Pure terminal data-readout/basis-change failures are UNSUPPORTED_REPAIR_CLASS:
the current product measurement cannot gain redundancy from extraction flags.
Mixed extraction/readout failures can try one additional full noisy terminal
verification round, with all gates, resets, readouts, temporal detectors and
resources accounted for. It cannot repair arbitrary non-CSS incompatible readout.
No ideal extraction-only ablation is used to inflate final distance.

The unchanged distance engine certifies claims. Every distance-increasing edge
also runs an independent boolean physical replay of every singleton, followed by
a separate exhaustive detector join through the claimed excluded weight. Class
heuristics never alter either certificate. Architecture/signature/class caches are
exact full-circuit keyed; tiny mutations are fully reevaluated because reset,
record and schedule changes make unproved local reuse unsafe.
