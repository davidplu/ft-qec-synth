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
