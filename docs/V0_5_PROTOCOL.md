# V0.5 prospective development protocol

Baseline: `67a7f2948d5df1d1096489a123adff2501789be6`, 113 passing tests.
All pre-existing source, tests, experiments, benchmarks, documentation and results
are recorded byte-for-byte in `results/v0.5/preservation.json` (1704 files; ignored generated egg-info excluded).
No held-out code or architecture will be imported. The supplied request ends
mid-sentence after its held-out rules; no missing rule is inferred.

## Certification

Retain VALID / INVALID / UNKNOWN, and Pareto objectives Q, D, QD, two_q_gates.
Exact type deduplication retains all physical locations. A minimum malignant set
cannot contain zero or repeated signatures; removing either would give a smaller
malignant set. Complete meet-in-the-middle joins followed by exact bipartite
location matching exclude each weight sequentially. Incomplete enumeration gives
only the last completed lower bound. Independently replay every upper witness.
For target <=4 use the V0.4 independent bit-lane exclusion verifier. Higher
targets require a separate independent certificate check; unsupported or capped
verification cannot count toward readiness.

Pilot: first UNKNOWN in each seed-10 primary task with UNKNOWNs, existing V0.4
records only. Four circuits had 8106–13890 physical variants, 1064–1907 unique
nonzero signature types. Target-3 certification required 4257–7629 work units
and 0.10–0.24 seconds, excluding signature generation. Saved in pilot.json.
Defaults therefore start at 8192 work units, then 65536, then 1048576; these
are measured type-join budgets, not repetitions of the old physical-pair cap.
Table limit 250000 entries.
Compression pilots: 32 edits took 156.8 seconds with exhaustive speculative
builds, and 70.1 seconds after component-cost queue ordering. Phase totals in
the latter were build 1.67s, ideal validation 4.91s, signatures 6.71s, native
certification 14.60s, independent verification 33.68s. The final design avoids
independent audits of intermediate points that are subsequently dominated;
every returned finalist is independently audited. A 256-evaluation cap is
therefore chosen as an explicit bounded development closure, not a guarantee
of minimality. Pilot raw records are retained separately from comparisons. Report work and peak table size, and measured
process memory separately; table entry counts are not bytes.

Certification is separate from the unchanged 48-slot search budget. Only
UNKNOWNs on the optimistic resource frontier are escalated, ordered by independent
metric extremes, frontier potential, lower-bound gap, and estimated type work.
Preserve the complete UNKNOWN frontier even if no certification budget remains.
Per replay run: 20 million certification work units; 256 new compression
evaluations. Limit outcomes remain explicitly bounded UNKNOWN/unresolved.

## Replay and descent

Replay all six V0.4 primary development tasks, seeds 10,11,12. Reuse frozen
V0.4 raw search traces (identical initial population, sequence, logic, 48 slots,
target 3), then promote relevant UNKNOWNs. This isolates endpoint recognition
from altered online search feedback. It is an offline native V0.5 certification
replay, not a claim about a changed online search trajectory.

After promotion, run supported single-edit compression on every valid Pareto
finalist. Rebuild circuits, compact physical ancillas and reschedule using the
existing builder; do not discard noisy operations or records based solely on
their apparent lack of detector relevance. Test every resource-reducing edit.
Keep Pareto tradeoffs across all four metrics. Queue processing yields after eight edits.
One implementation is returned per identical numerical resource point; all
alternative architectures remain in raw records. Certify intermediate edits with
the exact engine, then independently audit every returned finalist. Audit returned finalists after
descent. No valid reducing edit gives LOCALLY_PROTECTION_MINIMAL_1; any such
edit gives NOT_LOCALLY_PROTECTION_MINIMAL; budget/UNKNOWN failures give
UNRESOLVED_MINIMALITY. Never claim global optimality.
Optional bounded two-edit exploration is disabled in primary comparison;
single-edit closure is the primary endpoint. Record ancestry and all proposals.

## Higher-distance ladder and readiness

Use permanent development circuits only. Compare naive physical enumeration
against deduplicated joins on small cases; benchmark higher-distance attempts
under explicit work/table limits. Synthetic signature fixtures test the
algorithm but do not count as physical distance-5/7 demonstrations.
Constructed repetition channels, if used, have quantum distance 1 and must not
be presented as full quantum-distance-5/7 codes. Higher-distance readiness
requires meaningful unrelated physical memory circuits and independent checks.
Do not use the held-out 23,25,44 codes or their extraction information.

READY requires every user gate, especially rigorous unrelated meaningful
distance-7 certification and plausible held-out runtime/memory. If not achieved,
report NOT_READY_FOR_HELD_OUT; create neither an algorithm freeze nor a held-out
protocol. Save complete raw runs, certificate metadata, failures, runtime and
memory observations, and explain any uncompleted request explicitly.
