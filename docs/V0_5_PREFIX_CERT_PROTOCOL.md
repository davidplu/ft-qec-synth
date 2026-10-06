# Prospective existing-family prefix certification supplement

The verified-cat Shor 5x5 one-round circuit has an independently replayed
native weight-four witness: code distance five does not imply circuit distance
five. The three-round type search stopped at lower bound three. SAT checks
remain capped. No readiness claim is made from the parent code distance.

Use the **existing interval-flag family**, sorted interaction orders, one syndrome
ancilla, and a shared pool of flags. Apply the same generic rule to every check:
one interval `(0,p)` for each interaction position p=1..weight. This is the
already supported prefix-interval pattern, not a new extraction family or a
code-specific hand repair. Use Shor 5x5 and 7x7, rounds 1 and 3, Z observable,
all permanently development-only. No held-out architecture is inspected.

Pre-certification inventory pilot: 5x5 R1 has 923 types / 425503 possible type
pairs; R3 has 2979 / 4435731. 7x7 R1 has 1963 / 1925703; R3 has 6295 /
19810365. Thus fix the bounded type table at 500000 entries and work at 4000000
for this supplement, enough to test the smallest weight-four exclusion without
allocating the much larger pair tables. Larger capped cases remain UNKNOWN.

Independent path through weight four: enumerate physical-location channels and
their legal pairs using independently forward-replayed effects. For each pair
effect retain a <=12-edge representative family preserving disjointness from
every forbidden set of <=2 locations. Complete single/pair/triple/four-fault
tests then give an exclusion. This physical-pair representative algorithm is
separate from global type deduplication and type-subset MITM. Alias variants at
the same location/effect are equivalent; zero-effect variants can be removed
from any <=4-fault malignant set without changing its outcome. No stronger
lower bound is claimed after a cap. Limits: 16000000 physical pair/join work,
500000 pair-effect buckets. Save inventory hashes, circuit, witness, algorithm
version, runtime and process peak memory. This method supports through four,
and does not masquerade as a distance-seven verifier.

Also run the physical-variant SAT checker with the prior fixed 60-second /
30-deterministic-unit limits. Native, physical-pair and SAT evidence remain
separately attributed. Require independent success for a distance-five
demonstration; require the original meaningful distance-seven gate for readiness.
