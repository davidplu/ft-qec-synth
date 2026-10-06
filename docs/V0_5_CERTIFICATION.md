# Location-compatible exact certification

A physical fault variant has binary detector vector d and observable-flip vector
l. A malignant set uses distinct physical locations, XORs to d=0, and l != 0.
The selected observable is the existing memory experiment's physical product
readout; this is not automatically every logical channel of a quantum code.

## Exact signature compression

For minimum-distance search, zero (d,l) types can be deleted from a malignant
set. Two equal types can also be deleted together. Deletion preserves detector
and logical outcomes and preserves legality of the remaining physical locations.
Therefore a minimum set contains distinct nonzero types. This theorem permits
type-level enumeration, but does **not** permit selecting just one representative
physical variant for each type. Each type stores every physical location and a
legal variant there. Exact augmenting-path bipartite matching checks whether a
candidate collection of types has a simultaneous distinct-location realization.
Different variants with the same (d,l) at one location are equivalent for this
question; one representative there suffices. Multiplicity is retained through the
full input inventory and distinct-location lists, not used as a distance weight.

Weights are considered consecutively. Complete exclusion at all lower weights
means that an omitted nonminimal malignant set at the current weight cannot be
the first violation. A table cap, work cap or unfinished join never excludes the
unfinished weight. If no violation exists at any finite weight, the returned
bound remains the requested finite lower bound, rather than claiming infinity.

For weight w, hash all size floor(w/2) type subsets by detector XOR. Stream size
ceil(w/2) subsets, join equal detector XORs, require nonzero logical XOR and
disjoint types, then match physical locations. Replay every found witness using
the independent physical Boolean verifier.

With T nonzero types, table storage is O(binomial(T,floor(w/2))) entries and
streaming enumeration is O(binomial(T,ceil(w/2))). Collision joins add their
actual bucket products; these can dominate both combinatorial terms. Matching
is polynomial in the tiny candidate set and its physical-location edges.
This is an exact bounded method, not a claim of efficient certification at every
requested distance. Peak table entries are measured; operating-system peak
working set includes Python, circuit and signature storage as well.

## Independent checks and artifacts

Targets through 4 use independent forward Boolean physical effects. The new
low-weight checker groups equal detector outcomes by logical outcome before
joining distinct locations, and is cross-checked against V0.4's full physical
pair checker. A separate physical-pair kernel can exclude through weight four.
The optional CP-SAT model uses every physical variant, one variant per location,
detector parity constraints and a nonzero logical parity. Only INFEASIBLE proves
exclusion; OPTIMAL/FEASIBLE return replayable upper witnesses. Solver limits
leave UNKNOWN. A physical-location trellis also processes locations once and keeps the minimum
weight for each accumulated detector/logical state, and choose at most one legal
variant from each location. This verifier obtains effects from independent
forward Boolean replay. A cap returns verified=false, never a proof.

Certificates are recipes for complete rechecking, with circuit, fault model and
inventory hashes, target, algorithm version and limits. They are not succinct
proofs eliminating the need to rerun exclusion. The schema is
`benchmarks/certification_v5/certificate.schema.json`. Metadata checks reject
tampered circuits or inventories; every witness is physically replayed.

The logical-packing projection certificate is a different, general proof route.
It finds product-readout logical representatives modulo compatible stabilizers,
then records actual detector combinations equating each coordinate to the
selected logical observable. Exhaustive physical singleton effects bound each
fault's coordinate Hamming weight by a. With m coordinates, zero detectors and
a logical flip require all m coordinates to flip, hence at least ceil(m/a)
faults. Coordinates are diagnostic parities of existing readout records; they
add no physical operations or scientific detectors. The independent verifier
uses forward physical propagation, checks every detector identity and norm,
and physically replays a matching upper witness. Its artifact schema is
`benchmarks/certification_v5/projection.schema.json`.

`ftqec verify-certificate saved-certification.json` rechecks public serialized
bounds and witnesses instead of trusting stored verification flags. Projection
proofs use the direct identities; native MITM recipes rerun independent exclusion
and can remain unresolved when verification caps are reached.

## Compression scope

The primary closure uses all existing physical single-edit operators and fresh
builds/schedules. Its labels describe the supported vocabulary, not all possible
circuits. The queue covers independent resource extremes; other resource values
break equal-extreme ties so irrelevant identifier order does not repeatedly
favor shallow ancestors. Certification and new-child evaluation budgets remain
separate from the unchanged search trace.

The public interface adds a separately bounded canonical closure (default
1024 new design evaluations). It normalizes only omission sets, checks that
normalization preserves the full physical circuit hash, and reuses conclusive
certificates only for identical circuit hashes and targets. UNKNOWN records are
retried. This preserves order-sensitive circuit fields and original ID aliases.
The historical experiment retains separate 256, 128 and 1024-evaluation phases.

Optional `rescue.depth_two` runs only after a complete or explicitly bounded
single-edit phase. It saves both intermediate and final IDs and limits pair
evaluations; it is disabled in the primary comparison. `cleanup.disconnected_ancillas`
removes tensor-disconnected unobserved ancillary components, orphan operations,
records and dead dependency paths, compacts addresses and reschedules. It
deliberately retains unreferenced measurements on ancillas that interacted with
data: their quantum channels can affect faults even when their records are unused.
This cleanup utility is separately tested; primary comparison uses the existing
builder's unused-qubit compaction rather than adding a new cleanup operator.
