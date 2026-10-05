# V0.4 prospective resource-synthesis protocol

Written before implementation and comparative runs. Objective: return the
Pareto frontier of (Q, D, QD, two-qubit gates) subject to certified d_c >= target.
Distance above the requirement does not override resource dominance. UNKNOWN
is distinct from INVALID; a capped search is never evidence of validity.

## Additional family selected before implementation

Implement generic small verified cat-state extraction. A weight-w check uses
w GHZ ancillas, one controlled-P coupling per data qubit, X-parity syndrome
readout, and noisy Z0Zj verification measurements before data coupling.
Verification outcomes are retained as detectors; no postselection, ideal
verification, feed-forward or published decoder guarantee is assumed.
This changes the interaction topology and fault propagation, unlike adding
another interval to the existing single syndrome-control gadget. Ancillas can
be reused between checks. Verification can be ablated and must be recertified.
This is a tractable Shor-style candidate family, not an implementation of every
optimization in the cited papers. Only bounded development checks are used.

Sources: [Shor, 1996](https://arxiv.org/abs/quant-ph/9605011) and
[Prabhu and Reichardt, Quantum 7, 1154 (2023)](https://quantum-journal.org/papers/q-2023-10-24-1154/).
Their literature results motivate the vocabulary, not certificates for these circuits.

## Comparisons and fixed settings

Development Suite 2's six primary tasks, existing supplied bases, chosen
observable and physical product readout; R=3 mandatory rounds; target=3.
Seeds 10,11,12; 48 evaluation slots, six identical generic initial candidates.
Primary variants: unchanged V0.3, V0.4 bidirectional, resource, random.
V0.3 retains its 200000 combination/spectrum cap and all existing defaults;
V0.4 uses the same native cap, weight <=2 screening for the target, and a
separate uncapped physical replay exclusion audit for every reported finalist.
Different algorithms may spend different time per slot; report time and caps.
New V0.4 family/basis proposals are bounded at four per expansion. Archive
cap=12; per-run operator statistics never transfer across tasks or seeds.
The first three repair/compression proposals precede exploratory basis/family
proposals, then remaining proposals. Repair-only valid parents retain existing
protection and attempt additional flags; exhausted proposals consume duplicates.
All proposed evaluations, duplicates and ideal-circuit rejections consume slots.
Every structural edit receives a fresh deterministic ASAP dependency schedule;
no global optimal scheduling claim is made.

Secondary: three parent codes (Steane7, affine15_k1, simplex15_k7), X memory,
same seeds and 48 slots. Generic overprotected starts use full-interval flags
duplicated twice, separate syndrome ancillas, parallelism=1, and one extra
terminal noisy round. Certify them before inclusion, report any failures.
For each valid start compare repair_only and repair_compress, same candidate
and budget. Also compare both variants from a single bare cheap start.
Every generator must retain at least one physical measurement epoch. Omitting
an epoch removes its entire extraction gadget, not just its classical record.
R=3 means three mandatory time blocks, with no modeled idle faults; reducing
measured epochs does not certify realistic storage-noise protection.
Family-off and basis-off ablations use primary starts, tasks and seeds.
No starts are selected for observed savings. No task/seed replacement.

Finalists: independently audit physical witness replay and exclusion through
target-1; audit every supported single protection removal. A resource-cheaper
valid neighbor disproves local minimality. Any unresolved cheaper neighbor
prevents LOCALLY_PROTECTION_MINIMAL. Structural ideal-detector failures
are documented separately from actual low-weight malignant witnesses.

Report validity rates and per-metric minima, absolute values and ratios only
when both paired runs reach the target. Ratios do not imply a single circuit
achieves all four minima. No post-hoc statistical general-superiority claim.

## Operational readiness thresholds (do not change after results)

All tests and independent audits pass; >=80% target success on at least three
primary tasks from three distinct parent instances; valid-start compression
reduces minimum QD by >=10% in >=2 parents and >=2 seeds per parent, without
losing any initially certified target; report all other metric tradeoffs.
At least two tasks return >=2 distinct resource-tradeoff Pareto points.
Median 48-slot primary search <=120 seconds and no run >600 seconds.
Runtime feasibility at high held-out distance remains unestablished: readiness
also requires a justified certification scaling bound for higher target tiers;
low-order runtime alone cannot satisfy this condition. Held-out packages,
manual sequences and resource numbers remain unread. If any condition fails,
NOT_READY_FOR_HELD_OUT; do not write an algorithm readiness freeze.

## Frozen future held-out metrics

At each predeclared target and identical memory/fault model, report reachability,
independently certified frontiers, and ratios of independent minima Q,D,QD,N2Q
to the valid human frontier H. Missing valid output is failure, not a ratio.
Report pointwise weak/strict dominance in all four dimensions, not ratios alone.
QD ratio labels: >2 poor; (1.5,2] weak; (1.2,1.5] useful;
[0.9,1.2] near expert; <0.9 potentially improves expert frontier.
Labels are descriptive, not significance statements. Human baselines must use
the same target, noise locations, mandatory rounds, readout and cost durations;
otherwise report incomparable. No human resource numbers are used here.
