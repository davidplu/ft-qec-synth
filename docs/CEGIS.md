# Counterexample-guided synthesis in V0.2

The engine consumes only a stabilizer specification, a generic candidate, and its computed fault witness. No code name or known architecture is used to select a repair. The input generating basis is still fixed; its transformation is not part of V0.2.

## Witness information

`CounterexampleAnalysis` records the witness hash, physical fault weight, rounds/checks/gadgets, hook support and weight, implicated interaction positions and monitored intervals, triggered/cancelled flag records, measurement/reset/idle faults, actual scheduled gadget overlap, and evidence of completion by another single-data-error fault. These are computed from elementary signatures and circuit metadata. A “hook” here is a multi-data-qubit propagated error from one elementary fault; “independent completion” additionally checks that removing the completing fault destroys the undetected-logical condition. Neither label implies a unique causal explanation.

Every logical witness is replayed using independent boolean-array simultaneous-fault propagation. The verifier accepts serialized circuits and serialized physical faults; it does not use signature XOR as its verification mechanism. Small-code tests also run actual dense quantum states, noisy readout, resets, and destructive data measurements to validate the experiment's ideal reference parities and fault-induced logical outcomes.

## Repair library

- Same-check or interaction-order hooks: add a flag bracketing a whole check or an implicated prefix/suffix; redirect, reverse, or separate implicated interaction support.
- Flag cancellation or readout hiding: add another independent flag record or split an existing interval into two separately measured flag epochs. These operations can increase physical flag resources.
- Cross-check witnesses: serialize gadgets, separate syndrome-ancilla slots, or change implicated check ordering. An overlapping schedule is reported only when its time spans actually overlap; a cross-check witness alone is not proof that overlap caused it.

Up to four flag intervals per check are allowed in both random and guided mutations. The full-interval flag rule depends on check width, not code identity. Initial candidates still use the shared V0.1 generic generator. Final product-readout failures often have no implicated extraction check and cannot be repaired by this library; guided search then uses a recorded random fallback. There is no automatic fault-tolerant readout synthesis or sophisticated recovery circuit.

## Matched search and provenance

All strategies use the same seeded initial population, beam selection, maximum evaluation slots, mutation count, fault-search limits, and resource rules. The ablation strategies are random, resource-guided, CEGIS, and a uniformly mixed strategy. Initial proposals are marked `RANDOM` with operator `initial_population`. Each subsequent proposal records `RANDOM`, `RESOURCE_GUIDED`, or `COUNTEREXAMPLE_GUIDED`. Guided proposals carry parent ID, source counterexample ID, detected failure class, and repair operator.

Every proposal, including a duplicate served from the shared cache, consumes one evaluation slot. This prevents a strategy with more duplicates from receiving extra attempts. Unique evaluations and cached proposals are reported separately. Mutation count is budget minus initial population size, identical across matched runs. No equal wall-time guarantee is imposed: time is measured as a separate cost, and larger guided circuits can be slower. There is no default resource-only early pruning that could conceal higher FT quality; optional hard resource ceilings apply identically to every strategy.

The exploratory beam uses nondominance in certified distance lower bound plus resource objectives; a deterministic lexicographic tie-break allocates the finite beam. The reported target frontier first requires `lower_bound >= target_dc`, then compares Q, D, QD, and two-qubit gates. These independent minima are not a single feasible architecture; the frontier supplies actual joint resource vectors.

```text
initial := generic_generate(code, common_seed)
for each fixed evaluation slot:
    proposal := next initial candidate or mutate(selected beam parent)
    if guided and parent has a verified witness:
        classify witness; propose a generic targeted repair
    evaluate schedule/resources and bounded temporal fault signatures
    independently replay any witness
    evaluate deterministic decoder separately
    compare child with its parent and transported source witness
    record provenance, outcomes, runtime and cache status
    update exploratory beam and target-conditioned resource frontier
```

## Repair outcomes

A records elimination of the *specific source witness*. Its local faults are transported to unique semantic addresses using round, check, gate role, flag epoch and data target, rather than raw operation indices. Changed ancilla allocation is remapped. Removed/ambiguous locations and idle tick changes are explicitly untransportable, not credited as witness elimination.

B requires a certified child lower bound above the parent's witnessed upper bound. C compares certified lower bounds. D requires equal exact distances and strict resource improvement. The conservative `repair_success` metric counts B, C, or D. A is measured separately as witness elimination: fixing one witness while retaining an equally dangerous different witness is not a quality success. E records absence of B/C/D; the separate `equal_or_worse_witness` flag can coexist with a resource success at preserved distance. Rates include denominators by failure class and repair operator. Cached proposals remain in proposal-level rates and can be analyzed separately from the raw records.

These outcomes are local parent/child comparisons. They do not demonstrate an improvement in the strongest architecture reached by a whole run. The controlled experiment and paired multi-seed comparisons address that separate research question.
