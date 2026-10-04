# V0.3 prospective hypothesis and fixed experiment

Frozen before any V0.3 final experiment. Baseline: published annotated v0.2.0,
commit e6e9c746151552befa4105a3b02b30a1d4a5b2c9; all 74 baseline tests pass.
Old V0.2 outputs are immutable.

Hypothesis: reducing fully enumerated minimum-weight malignant classes allows
neutral repairs to compose into higher certified circuit-distance tiers.

Development inputs: css4, noncss4, perfect5, steane; both X/Z memories, R=3,
ideal encoded input, physical product readout, no implicit idles. Seeds 0–5.
Target d_c=3, maximum fault weight 3, certification cap 200000 work entries,
spectrum cap 200000, 32 evaluation slots including six common initial candidates.
Beam 12; at most four protected progress entries for four slots; compound depth
at most three; at most four diverse representative classes and 16 repair options
per parent; four flags/check; at most one added noisy terminal extraction round.
Duplicates consume slots. Runtime is measured, not equalized. All strategies use
the same physical mutation library and certification standards.

Primary strategies: RANDOM, RESOURCE_GUIDED, V0.2_CEGIS, V0.3_CEGIS, MIXED.
V0.2_CEGIS retains its source-witness queue and old quality/resource selection.
New strategies use structural classes, protected progress, dominant diverse
witnesses, greedy estimated coverage and within-run operator memory. MIXED uses
one third random exploration. Baseline strategies receive the new boundary
mutation with the same random availability; results are a contemporary matched
comparison, not a replay of V0.2 raw files.

Success is predefined: V0.3 must beat each of RANDOM, RESOURCE_GUIDED and
V0.2_CEGIS on at least one of (a) target attainment, (b) target evaluations with
unreached assigned budget+1, (c) highest rigorous lower bound, (d) minimum QD at
the common attained distance tier. Use two-sided exact paired sign tests and
Holm correction over all 12 primary endpoint/comparator tests at family alpha
0.05. Direction must favor V0.3; favorable cases must span at least two codes and
three seeds. QD comparisons exclude tier 1 and report unmatched target failures.
No endpoint, budget, seed or criterion will be changed after inspecting outcomes.

Matched ablations use the same six seeds and 32 slots: raw vs signature vs
structural equivalence; no progress protection; arbitrary rather than dominant
class ordering; no coverage prioritization. Structural default is shared with
the primary experiment. No post-result tuning or reruns to obtain a win.

Direct gradient analysis is descriptive, not causal: for evaluated parent-child
edges, measure descendant distance gain conditional on complete minimum-layer
count decrease vs nondecrease, censored at run end; report exposure differences
and count-reduction magnitude versus descendant gain. Reconstruct every gain
chain, including neutral intermediate steps, from evaluation-node ancestry.

Readiness additionally requires all tests, independent witnesses and exclusion
verification, intact semantics, uncontaminated held-out information and practical
scaling evidence. No held-out input is read or run. Small development timing alone
does not establish held-out-scale throughput. Without that evidence return
NOT_READY_FOR_HELD_OUT even if a development endpoint passes.
