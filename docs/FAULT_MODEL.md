# V0.2 repeated-memory fault model

## Experiment and rounds

The default is R=3 complete extraction rounds, independent of code distance. `MemoryConfig` and the CLI expose R explicitly. A round measures every specified stabilizer once using the candidate's check order, support order, ancilla allocation, flag intervals and parallel lanes; a global zero-duration barrier ends the round. Every flag interval is reset, opened, closed and measured in each round. No round is silently omitted or replaced by an ideal syndrome measurement. The result records rounds, basis, logical index, noisy-input setting and idle policy.

Input is an ideal encoded +1 stabilizer state with the selected logical X_i or Z_i in its +1 eigenstate. Other logical degrees of freedom need not be fixed. There is no hidden noisy encoder circuit. Optional `noisy_input` adds an explicit unit-time local Pauli output-noise layer after that ideal encoded preparation, labelled preparation noise; this is not a proof of fault-tolerant preparation. All syndrome/flag preparations use noisy RESET-to-|0> plus basis gates where required.

Final readout measures every data qubit destructively in a physical Pauli basis. On support of the selected logical representative, that basis is its local X/Y/Z; remaining sites use the experiment's X or Z basis. X readout uses H then M; Y readout uses SDG then H then M. Those basis gates and every final measurement are noisy. One logical index is measured per experiment; run both X/Z and all desired indices separately for k>1.

## Temporal detectors and logical observable

Initial detector for S_i is s_i(0), against the ideal +1 input check. Inter-round detector is s_i(r-1) XOR s_i(r). Flag records are separate detectors in each fresh epoch, not differenced across resets. A final detector is s_i(R-1) XOR the parity of terminal data records on S_i's support **only if every local Pauli of S_i matches the physical readout basis**. No other ideal final syndrome is appended in repeated-memory mode. Non-CSS product readout can lack enough compatible checks and yield a genuine low-distance terminal readout experiment; this limitation is reported rather than closed by fictitious measurements.

The logical observable is the parity of actual final data records on the selected logical representative, relative to its intended +1 stored eigenvalue. Fault signatures track its flip, not membership of the final data Pauli in the stabilizer group. A decoder-independent circuit-distance witness has zero full temporal/flag detector signature and nonzero logical-observable effect. Nonzero-detector events can fail a decoder without being distance witnesses.

## Allowed physical faults

One-qubit Clifford/Pauli/explicit-IDLE locations admit X, Y or Z after the ideal gate. Two-qubit CX/CZ/SWAP locations admit all 15 nonidentity two-qubit Paulis after the gate. RESET and PREP erase prior local Pauli errors, prepare |0>, then admit X/Y/Z output faults. Z at |0> can be a harmless duplicate; variants remain explicit. Measurement faults flip the classical Z readout bit only, with no additional quantum backaction fault. Final data readout uses the same model as syndrome/flag readout. Pauli phases are ignored for error deviations.

Optional implicit idle noise adds X/Y/Z at each unoccupied unit-duration scheduler tick, on all allocated qubits, including trailing storage. Idle addresses include physical qubit and tick; round metadata follows the actual round time span. Propagation anchors the event before that qubit's next operation, or after the circuit when it has no later use. Operations on other qubits commute with this insertion. A fault after a qubit's final physical measurement cannot alter its already recorded outcome. Zero-duration barriers are not noisy locations.

A fault set contains at most one variant per physical gate/readout/idle location. This is adversarial physical-location weight, not a stochastic noise probability or LER. It includes noisy ancilla preparation/reset, gates and measurement, and optionally noisy encoded-input output locations and storage. It does not include correlations between distinct locations unless their combination is explicitly enumerated.

## Signatures, search and verification

Elementary signatures use packed temporal detector bits, the selected logical bit, flag-record effects and final Pauli-support coordinates. A backwards Clifford/reset/measurement transfer map builds these signatures efficiently. The retained forward single-fault simulation and independent simultaneous-fault boolean-array replay use different algorithms/representations. Dense-state tests independently validate noiseless reference parity and actual fault effects on small CSS/non-CSS circuits, including flag epochs.

Weights 1 and 2 use syndrome grouping; weight 3 matches pair XOR against singleton syndrome groups and excludes same-location combinations. Tractable weights 4–6 use bounded direct signature combinations, never repeated circuit simulation. Exhausted layers alone advance the lower bound. A t-fault witness gives d_c <= t; exhaustive exclusion through t gives d_c > t. EXACT requires matching integer bounds. Work limits and incomplete layers are explicit. Every witness reported by repeated-memory search is independently replayed; standalone `faults` also reports verification.

## Decoder metric

The bounded minimum-weight decoder learns a deterministic detector-to-logical recovery table from completely enumerated low-weight layers. A minimum-weight tie chooses the numerically smallest logical effect. It never calls an unseen or partially trained detector signature a resolved prediction. Its complete-layer coverage, resolved cases, failures and nonzero-syndrome failure witnesses are separate from circuit-distance results. Recovery means a logical-frame correction; no physical recovery circuit is synthesized. Enumerated failure counts are not a stochastic logical-error rate.

## Resources and scheduling

All allocated data, syndrome and flag slots count toward Q. Every gate, measurement, reset, explicit input-noise/IDLE location occupies one tick; barriers have zero duration. Implicit idles are noise locations without adding explicit operations. D spans preparation/output-noise if enabled, all R rounds, final basis rotations and final data measurements. QD is Q times D; gate and measurement/reset counts include all rounds and final readout. Ancilla reuse retains its causal dependencies. Hardware durations remain unused in this unit-time model.

Imported custom IR must establish its own ideal reference parity/encoded-memory semantic contract. Structural validation alone does not prove it. Generated gadgets and repeated-memory construction are independently tested. The explicit legacy `--model ideal-boundary` mode retains the V0.1 experiment below and is not mixed into V0.2 benchmark frontiers.

---

# Legacy V0.1 model (explicit compatibility mode)

# V0.1 fault, boundary and resource definitions

## Boundary experiment

One extraction round starts in the +1 eigenspace of all specified checks with ideal initialization. The reference trajectory has zero syndrome and flag records. Detectors comprise configured measurement-record parity groups plus an **ideal final stabilizer syndrome of the data**. The final boundary is conceptual and adds no gates/resources/fault locations. Initial syndrome is fixed, ideal and fault-free. Measurement records from the generated check gadgets are detectors against this ideal zero reference. This experiment can be more informative than a deployable repeated-round circuit; bounds must always carry this label.

Final logical effect consists of symplectic commutation with a computed logical X/Z basis, and any explicit record-parity observables. Logical projection is meaningful as a logical coset when final syndrome vanishes; nonzero-syndrome signatures are intermediate linear coordinates only. Witnesses require zero total detector signature and nonzero logical effect. Flag records are detectors too, so a logical witness has zero total flag parity, although individual faults can fire flags that cancel.

## Physical locations

A faulty one-qubit Clifford contributes one of X/Y/Z **after** its ideal gate. A two-qubit gate contributes any of 15 nonidentity two-qubit Paulis after the gate. PREP and RESET set |0>, erase prior local errors, then admit X/Y/Z output faults. Z faults at a |0> output are harmless duplicate variants; they are retained for explicit model completeness. M is nondestructive Z measurement with one classical readout-bit flip fault. No separate quantum measurement backaction fault is included. H implements X measurement via basis rotation. Pauli gates, SWAP, CX and CZ are supported. Global Pauli phases have no effect on fault signatures.

Fault sets use distinct physical locations. Different variants at the same gate cannot be combined as two independent faults. Optional idles contribute X/Y/Z at each unoccupied unit-duration schedule tick on every physical qubit, including trailing data storage. Idle faults are injected before the next operation on that qubit (or at the final boundary). This is equivalent for Pauli propagation because intervening operations touch other qubits. Trailing ancilla errors have no data effect after their last measurement. Prep/reset before storage clear earlier errors.

Bit-packed signatures are linear under XOR for this non-adaptive Clifford/measurement/reset model. Singles are enumerated, pairs hash equal detection keys, triples match pair XOR against singleton detection keys. The search returns the first reproducible witness. Work limits count tested singleton/pair/triple entries (including unsuccessful pair lookups), not wall time; a completed layer alone advances the lower bound.

## Resource accounting and scheduling

All physical data/syndrome/flag slots count toward Q even when idle. Flags are pooled per syndrome slot. All preparations, measurements, resets, 1Q/2Q operations and IDLE operations occupy one tick; BARRIER is zero duration and synchronizes its specified qubits and explicit dependencies. Scheduled depth is the maximum finish time. QD = Q times depth. Gate counts exclude preparation/reset/measurement from 1Q gates and report them separately. Operation count excludes barriers and includes all other explicit IR operations. Implicit schedule idles are fault locations when enabled and do not inflate explicit operation count.

The greedy schedule preserves per-qubit operation order and explicit backward dependencies. Each generated gadget is causally serial; checks can overlap on different data/ancilla slots and parallel lanes. Lower bounds use maximum qubit workload, two-qubit capacity conflicts and explicit dependency chains. Efficiency = lower bound / actual depth (at most 1), with 1 for an empty circuit. Unit-time schedules do not use optional hardware durations.

No decoding, corrective recovery, adaptive feed-forward, repeated noisy boundaries or logical error-rate estimates are provided. Undetected-logical distance does not exclude two same-syndrome faults requiring incompatible corrections. Full FT correction requires this additional distinguishability analysis.

Custom imported circuits must preserve the intended encoded subspace and supply deterministic reference measurement parities. The tool checks IR structure, not this full noiseless semantic contract. Generated extraction gadgets satisfy the contract by construction. Bounds on an arbitrary imported IR without establishing that contract are only Pauli-deviation results.
