"""Independent simultaneous-fault replay, with one bit lane per witness.

This interprets the physical circuit for all witnesses together. It neither
builds suffix maps nor XORs optimized signatures. Each lane is the same boolean
state machine as the scalar independent replay.
"""
from .verification import validate_fault_address
from .signatures import Fault
from ..codes.logicals import logical_basis
from ..codes.pauli import Pauli


def replay_lanes(circuit, groups):
    circuit.validate()
    groups = [[Fault.from_dict(f) if isinstance(f, dict) else f for f in group] for group in groups]
    # Scalar replay's validator checks every distinct physical address/type,
    # virtual idle placement. This validation is shared, never omitted.
    unique = {f for group in groups for f in group}
    for f in unique: validate_fault_address(circuit, f)
    events = {}
    for lane, group in enumerate(groups):
        if len({f.location for f in group}) != len(group): raise ValueError('Repeated physical fault location')
        for f in group:
            entry = events.setdefault(f.operation, {})
            entry[f] = entry.get(f, 0) ^ (1 << lane)
    x = [0]*circuit.num_qubits; z = [0]*circuit.num_qubits; records = {}
    def inject(f, mask):
        for q,p in zip(f.qubits, f.label):
            if p in 'XY': x[q] ^= mask
            if p in 'YZ': z[q] ^= mask
    for i, op in enumerate(circuit.operations):
        at = events.get(i, {})
        for f,mask in at.items():
            if f.before: inject(f,mask)
        gate = op.gate; a = op.qubits[0] if op.qubits else 0
        if gate in ('PREP','RESET'): x[a]=z[a]=0
        elif gate == 'M':
            flip = 0
            for f,mask in at.items():
                if f.kind == 'measurement': flip ^= mask
            if op.record: records[op.record] = x[a] ^ flip
        elif gate == 'H': x[a],z[a]=z[a],x[a]
        elif gate in ('S','SDG'): z[a] ^= x[a]
        elif gate == 'CX':
            b=op.qubits[1];x[b]^=x[a];z[a]^=z[b]
        elif gate == 'CZ':
            b=op.qubits[1];z[a]^=x[b];z[b]^=x[a]
        elif gate == 'SWAP':
            b=op.qubits[1];x[a],x[b]=x[b],x[a];z[a],z[b]=z[b],z[a]
        for f,mask in at.items():
            if not f.before and f.kind!='measurement':inject(f,mask)
    for f,mask in events.get(len(circuit.operations),{}).items():inject(f,mask)
    def parity(names):
        result=0
        for name in names:result^=records.get(name,0)
        return result
    def symplectic(pauli):
        result=0
        for q in range(circuit.code.n):
            if pauli.x >> q & 1:result^=z[q]
            if pauli.z >> q & 1:result^=x[q]
        return result
    detectors=[parity(d) for d in circuit.detectors];logical=[]
    if circuit.boundary_model=='ideal_initial_and_final_syndrome':
        detectors += [symplectic(g) for g in circuit.code.generators]
        for a,b in logical_basis(circuit.code): logical += [symplectic(b),symplectic(a)]
    logical += [parity(o) for o in circuit.observables]
    flags=[records[r] for r in sorted(records) if r.startswith('f')]
    return {'detectors':detectors,'logical':logical,'flags':flags,
            'data_x':x[:circuit.code.n],'data_z':z[:circuit.code.n],
            'fault_addresses':len(unique)}


def singleton_effects(circuit, faults):
    """Physical circuit interpretation, one independent singleton per lane."""
    actual=replay_lanes(circuit,[[f] for f in faults])
    return [(sum(((mask>>i)&1)<<j for j,mask in enumerate(actual['detectors'])),
             sum(((mask>>i)&1)<<j for j,mask in enumerate(actual['logical'])))
            for i in range(len(faults))]


def verify_batch(circuit, witnesses):
    for w in witnesses:
        if w['fault_count']!=len(w['faults']):raise ValueError('Fault weight mismatch')
    actual=replay_lanes(circuit,[w['faults'] for w in witnesses])
    detectors=actual['detectors'];logical=actual['logical'];flags=actual['flags']
    x=actual['data_x'];z=actual['data_z']
    def expected_masks(key,width):
        masks=[0]*width
        for lane,w in enumerate(witnesses):
            value=w[key]
            if value >> width:raise ValueError('Expected effect exceeds circuit dimensions')
            for bit in range(width):
                if value >> bit & 1:masks[bit] |= 1<<lane
        return masks
    agrees = (detectors==expected_masks('detector_outcomes',len(detectors)) and
              logical==expected_masks('logical_coset',len(logical)) and
              flags==expected_masks('flag_outcomes',len(flags)))
    expected_x=[0]*circuit.code.n;expected_z=[0]*circuit.code.n
    for lane,w in enumerate(witnesses):
        p=Pauli.parse(w['final_data_pauli'])
        if p.n!=circuit.code.n:raise ValueError('Expected data Pauli has wrong size')
        for q in range(p.n):
            if p.x >> q & 1:expected_x[q] |= 1<<lane
            if p.z >> q & 1:expected_z[q] |= 1<<lane
    agrees &= x[:circuit.code.n]==expected_x and z[:circuit.code.n]==expected_z
    malignant = all(w['detector_outcomes']==0 and w['flag_outcomes']==0 and w['logical_coset']!=0 for w in witnesses)
    return {'verified': bool(agrees and malignant),'witnesses':len(witnesses),
            'physical_fault_addresses_validated':actual['fault_addresses'], 'method':'independent_simultaneous_bit_lane_boolean_replay'}
