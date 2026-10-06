"""Render measured phase comparisons without pooling distinct protocols."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'results/v0.5'
def main():
    a=json.loads((OUT/'aggregate.json').read_text());f=a['final_closure'];rows=f['runs_table']
    text='''# FTQEC V0.5 results

**NOT_READY_FOR_HELD_OUT.** V0.5 recognizes certified target-3 architectures
in all 18 preserved V0.4 traces, versus 9 native V0.4 successes. Meaningful
unrelated selected-X-readout memory experiments have independently verified
exact circuit distances 5 and 7. Generic distance-7 certification feasibility
for the future 23-qubit task remains unestablished. No held-out architecture
was inspected, no held-out experiment was run, and no held-out freeze or
protocol was created.

## Preservation and comparison design

Baseline commit: `67a7f2948d5df1d1096489a123adff2501789be6`.
The original 113 tests passed before changes. All 1704 retained historical
file hashes verify. Five ignored generated packaging metadata files were
explicitly excluded from active preservation hashes; their original hashes
remain recorded. Historical scientific source, tests, protocols and results
remain unchanged. New implementation lives in `certification_v5`.

Six development tasks times seeds 10/11/12 replay the exact V0.4 initial IDs,
48 evaluation slots, target 3, code and memory definitions. This is offline
endpoint recognition; it does not show an advantage from changed online search
feedback. The six tasks share code parents and the three seeds are not
independent code families. These are observed finite development results.

`V0_5_PROTOCOL.md` and `experiment_snapshot.json` freeze the original source
set before primary results. New supplemental protocols were written before
their respective runs. `v05_reproduce.py --verify-only` verifies the recorded
source set despite later additive modules. Omitting that flag reruns into a
separate directory; it never overwrites original raw results.

## Certification architecture and staged recognition

The exact engine enumerates nonzero distinct detector/logical signature types,
retaining every physical location alias. Removing zero or repeated identical
types preserves a minimum malignant set. Exact bipartite matching enforces
distinct locations; scalar physical replay checks each witness. Consecutively
completed weights establish lower bounds. Caps preserve the last completed
bound and leave UNKNOWN, never inferred validity.

Relevant optimistic UNKNOWN points receive deterministic metric-extreme,
distance-gap and expected-work priority. Pilot-based tiers are 8192, 65536 and
1048576 native work units, within a separate 20000000-unit run budget. Search
slots and new compression design evaluations are separately counted. Promotion
increased native recognition from 9/18 to 18/18 without weakening the target.
For the nine already-valid runs, median coordinate-minimum resource ratios
after promotion were all 1.0; the gain is recognition/completeness.

## Compression and frontier completeness

The original primary descent has 256 new evaluations. A separate 128-evaluation
completion and then a separate 1024-evaluation canonical closure were retained.
Canonical normalization changes only set-like omissions and requires identical
full circuit hashes. Conclusive evidence is reused only for the same physical
circuit and target. Every actual edit rebuilds and reschedules the circuit.
All supported physical single edits are considered; speculative ranking uses
cost estimates, never accepted resource values. Eight-proposal batches allow
descendants to enter the queue. One implementation represents each equal
numeric resource point; alternative genomes remain in raw records.

Primary results: 22 returned points, 4 locally minimal and 18 unresolved.
After the two supplemental phases, 37 points remain: 17 locally minimal,
14 explicitly nonminimal, and 6 unresolved. Thus only 45.95% of returned
points have a completed single-edit minimality certificate; do not call most
finalists minimal. Nonminimal points can remain Pareto tradeoffs because an
edit improves one coordinate while worsening another. The two capped runs
retain the 1024-evaluation cap; a separate post-run inventory lists 196
uncertified remaining neighbors of their six unresolved finalists without
modifying raw certificates or labels. All 37 final
points independently exclude every legal weight-1/2 physical fault set.

No Pareto-relevant UNKNOWN remains in the *evaluated archive*. This is not
proof of an exhaustive supported architecture frontier: unevaluated neighbors,
omission vocabulary and finite work remain boundaries. The optional depth-two
rescue and tensor-disconnected cleanup utility are tested but disabled in the
primary comparison. Existing builder compaction is used in all primary runs.

Median final coordinate-minimum ratios relative to the promoted endpoints:
'''
    text+='\n| Q | D | QD | two-qubit gates |\n|---:|---:|---:|---:|\n'
    text+='| '+' | '.join(f"{f['median_resource_ratio_from_promotion'][m]:.6f}" for m in ('Q','D','QD','two_q_gates'))+' |\n'
    text+='\nThese are separate coordinate minima, potentially attained by different circuits. They are not a single architecture with all four minima.\n\n'
    text+='| Task / seed | valid | UNKNOWN | minimal | nonminimal | unresolved | Q min | D min | QD min | 2Q min |\n|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|\n'
    for t in rows:
        name=t['run'].replace('primary--','').replace('--v04--',' / ').replace('.json.gz','');l=t['labels'];m=t['canonical_minima']
        text+='| '+name+' | '+' | '.join(str(x) for x in (t['valid_points'],t['unknown_points'],l.get('LOCALLY_PROTECTION_MINIMAL_1',0),l.get('NOT_LOCALLY_PROTECTION_MINIMAL',0),l.get('UNRESOLVED_MINIMALITY',0),m['Q'],m['D'],m['QD'],m['two_q_gates']))+' |\n'
    text+='''
## Unrelated higher-distance certificates and negative controls

Standard Shor square codes on 25 and 49 data qubits are permanent development
proxies. They are distinct from reserved held-out inputs, and no new code
family is claimed. Their quantum distances 5/7 follow analytically: inner ZZ
checks force an X normalizer to be constant within blocks; outer adjacent-block
X checks force Z parities to agree across blocks. A nontrivial logical X uses
one entire block, and a logical Z uses one qubit per block, both weight m.
Any nontrivial normalizer coset therefore has weight at least m.

For both the existing interval and verified-cat families, R=1 and R=3,
the selected X-readout memory has m disjoint logical coordinates and maximum
single-fault coordinate norm 1. Actual detector identities force all coordinates
to flip in a malignant set. This proves lower bound m for every legal physical
fault set; m final measurement flips provide replayable matching upper bounds.
Independent forward physical propagation checks every identity and every
singleton. No ideal detectors were added. This certifies one selected memory
observable, not both quantum-memory channels or all extraction behavior.

All 16 prespecified projection cases are retained: eight X cases are exact 5/7,
eight Z cases have weak projection bound 1 and matching readout upper 5/7.
The independent projection proof does not claim those Z upper bounds are exact.
Separate native/pair/SAT controls expose low-distance Z extraction faults:
the prefix-flag cases all have exact distance 3, and Shor5 R1 cat has native
exact distance 4. These witnesses physically replay. Full physical CP-SAT
attempts with 60-second/30-deterministic-unit caps did not independently prove
the requested larger exclusions. OPTIMAL in feasibility models denotes a
found violating assignment, not a minimum-distance proof.

Repetition selected channels reach 5/7 but their parent quantum distance is 1;
they are algorithm checks and do not count as the meaningful proxy evidence.

## Performance and scaling

For T distinct types, weight-w MITM tables require
O(binomial(T,floor(w/2))) entries and streaming work
O(binomial(T,ceil(w/2))) plus detector bucket collision products and exact
location matching. Table/work caps are explicit. The independent physical-pair
kernel preserves disjointness against two forbidden locations with at most 12
edges per detector/logical bucket. CP-SAT and physical trellis offer independent
routes but remain bounded on the harder proxies.

The measured native promotion pilot had 1064–1907 types and 4257–7629
work units. A 32-edit pilot identified repeated building, signature retention
and unnecessary audits of dominated intermediates as bottlenecks. Saved pilots
retain the before/after timings. The forward low-weight audit on one 13890-variant
cat case took 0.6125 s versus 0.7004 s for the old physical-pair audit.
Primary median run time was 112.77 s. Total measured primary plus supplemental
run times sum to 2213.18 s; the maximum per-run phase sum is 256.16 s.
Concurrent process contention makes these observed wall times, not a controlled
hardware speed benchmark. Native profile records distinguish subset work,
joins, location checks and peak table entries; compression records retain
build, ideal, signature, certification and final verification timings.

Positive projection certificate profiles (signature construction included;
independent verification and upper search separately saved):

| Proxy | physical variants | certificate seconds | process peak MiB |
|---|---:|---:|---:|
'''
    for r in a['projection_ladder']:
        if r['exact']:text+=f"| {r['name']} | {r['physical_variants']} | {r['certificate_seconds']:.4f} | {r['peak_process_bytes']/2**20:.2f} |\n"
    text+='''
Process peaks are cumulative high-water marks within each ladder process, not
isolated per-certificate allocation measurements. Maximum recorded projection
process peak was 137.45 MiB across positive and negative cases.

## Readiness, limitations and reproducibility

The exact distance-5/7 selected-channel gates now have rigorous meaningful
unrelated examples with independent checks. The remaining scaling gate fails:
disjoint logical representatives of weight at least 7 fit at most floor(23/7)=3
times on 23 data qubits, so this packing proof alone cannot certify distance 7
there. Generic MITM/SAT feasibility at that scale is unestablished. Public
online search still supports targets 2–4; standalone certification accepts
higher targets with explicit caps. Higher-distance synthesis is unfinished.
No held-out freeze or protocol is produced while NOT_READY.

Ideal encoded input, selected logical basis/index, physical final readout,
existing location fault model and no-idle default remain unchanged. Unit-time
resource metrics are abstract, without routing, hardware mapping or LER claims.
No new extraction family or stabilizer-basis algorithm was introduced. Search
priority is a deterministic heuristic, not a calibrated information-gain model.
Cleanup and depth-two demonstrations are limited tests rather than a measured
general search advantage. Global optimality and full frontier completeness
remain unclaimed.

Raw artifacts: `results/v0.5/raw`, `completion`, `canonical_completion`,
`projection_ladder`, `sat_ladder`, `prefix_ladder`, pilots and original ladder.
`aggregate.json` gives every phase, coordinate minimum, label and UNKNOWN ID.
`final_physical_verification.json` freshly checks 84 endpoints across all three
phases, all 16 projection proofs and higher witness artifacts.
`pending_neighbor_inventory.json` bounds the remaining supported single edits
for every unresolved finalist; it performs no certification.
`final_tests.xml` and `test_verification.json` record the complete final suite.
`artifact_manifest.json` hashes saved artifacts; `packaging_verification.json`
records the final wheel and isolated installed-interface smoke check.

Reproduce verification with:

```console
python experiments/v05_reproduce.py --verify-only
python experiments/v05_final_audit.py
python experiments/v05_final_report.py
python experiments/v05_results_document.py
pytest
```

Use the original and supplemental scripts only in a preserved copy when
re-running timings; existing raw files are retained by their skip/resume logic.
Consult each prospective protocol for exact phase caps and scope.
'''
    (ROOT/'docs/V0_5_RESULTS.md').write_text(text,encoding='utf-8')
if __name__=='__main__':main()
