"""Slow independent boolean-array simultaneous-fault replay.

This path neither constructs nor combines optimized fault signatures.
"""
from ..circuits.model import Circuit
from ..codes.pauli import Pauli
from ..codes.logicals import logical_basis, logical_effect
from .signatures import Fault
from ..scheduling.scheduler import schedule


def replay(circuit, faults):
    c = Circuit.from_dict(circuit) if isinstance(circuit, dict) else circuit
    faults = [Fault.from_dict(f) if isinstance(f, dict) else f for f in faults]
    c.validate()
    if len({f.location for f in faults}) != len(faults):
        raise ValueError('Multiple faults at the same physical location')
    for f in faults: validate_fault_address(c, f)
    x = [False]*c.num_qubits
    z = [False]*c.num_qubits
    records = {}
    def inject(f):
        for q, p in zip(f.qubits, f.label):
            if p in 'XY': x[q] = not x[q]
            if p in 'YZ': z[q] = not z[q]
    events = {}
    for f in faults: events.setdefault(f.operation, []).append(f)
    for i, op in enumerate(c.operations):
        at = events.get(i, ())
        for f in at:
            if f.before: inject(f)
        g = op.gate
        a = op.qubits[0] if op.qubits else 0
        if g in ('PREP', 'RESET'): x[a] = z[a] = False
        elif g == 'M':
            if op.record: records[op.record] = int(x[a]) ^ (sum(f.kind == 'measurement' for f in at) & 1)
        elif g == 'H': x[a], z[a] = z[a], x[a]
        elif g in ('S', 'SDG'): z[a] ^= x[a]
        elif g == 'CX':
            b = op.qubits[1]; x[b] ^= x[a]; z[a] ^= z[b]
        elif g == 'CZ':
            b = op.qubits[1]; z[a] ^= x[b]; z[b] ^= x[a]
        elif g == 'SWAP':
            b = op.qubits[1]; x[a], x[b] = x[b], x[a]; z[a], z[b] = z[b], z[a]
        for f in at:
            if not f.before and f.kind != 'measurement': inject(f)
    for f in events.get(len(c.operations), ()): inject(f)
    detector_bits = [sum(records.get(r, 0) for r in d) & 1 for d in c.detectors]
    error = Pauli(c.code.n, sum(int(x[q]) << q for q in range(c.code.n)),
                  sum(int(z[q]) << q for q in range(c.code.n)))
    legacy = c.boundary_model == 'ideal_initial_and_final_syndrome'
    if legacy:
        detector_bits.extend(g.symplectic(error) for g in c.code.generators)
    logical = logical_effect(error, logical_basis(c.code)) if legacy else 0
    offset = 2*c.code.k if legacy else 0
    logical |= sum((sum(records.get(r, 0) for r in obs) & 1) << (offset+i) for i, obs in enumerate(c.observables))
    flag_names = sorted(r for r in records if r.startswith('f'))
    flags = sum(records[r] << i for i, r in enumerate(flag_names))
    return {'detector_outcomes': sum(b << i for i, b in enumerate(detector_bits)),
            'flag_outcomes': flags, 'logical_coset': logical, 'final_data_pauli': str(error),
            'measurement_record_effects': records}


def verify_witness(circuit, witness):
    actual = replay(circuit, witness['faults'])
    expected_keys = ('detector_outcomes', 'flag_outcomes', 'logical_coset', 'final_data_pauli')
    agrees = all(actual[k] == witness[k] for k in expected_keys)
    return {'verified': agrees and actual['detector_outcomes'] == 0 and actual['logical_coset'] != 0,
            'agrees': agrees, 'actual': actual}


def validate_fault_address(c, f):
    """Validate one physical address on an already validated circuit."""
    if not 0 <= f.operation <= len(c.operations) or len(f.label) != len(f.qubits):
        raise ValueError('Invalid fault address')
    if any(q < 0 or q >= c.num_qubits for q in f.qubits) or any(p not in 'IXYZ' for p in f.label):
        raise ValueError('Invalid fault Pauli')
    if f.kind == 'measurement':
        if f.operation == len(c.operations) or c.operations[f.operation].gate != 'M' or f.label != 'I':
            raise ValueError('Invalid readout fault')
        if f.before or f.qubits != c.operations[f.operation].qubits:
            raise ValueError('Invalid readout fault address')
    elif f.kind != 'idle':
        if f.operation == len(c.operations) or tuple(f.qubits) != c.operations[f.operation].qubits or f.before:
            raise ValueError('Invalid gate fault')
        if all(p == 'I' for p in f.label) or c.operations[f.operation].gate in ('M', 'BARRIER'):
            raise ValueError('Invalid gate fault type')
        expected_kind = 'preparation' if c.operations[f.operation].role == 'input_preparation_noise' else 'idle_gate' if c.operations[f.operation].gate=='IDLE' else c.operations[f.operation].gate.lower()
        if f.kind != expected_kind: raise ValueError('Fault kind does not match gate')
    if f.kind != 'idle' and f.location != f'op:{f.operation}':
        raise ValueError('Forged physical location identifier')
    if f.kind == 'idle':
        if len(f.qubits) != 1 or f.label not in 'XYZ' or not f.before:
            raise ValueError('Invalid idle fault')
        try:
            tag, qubit, tick = f.location.split(':')
            qubit, tick = int(qubit), int(tick)
        except (ValueError, AttributeError): raise ValueError('Invalid idle location') from None
        sched = schedule(c)
        if tag != 'idle' or qubit != f.qubits[0] or not 0 <= tick < sched.depth:
            raise ValueError('Idle tick outside circuit')
        uses = [(sched.starts[i], i) for i, op in enumerate(c.operations)
                if qubit in op.qubits and op.gate != 'BARRIER']
        if any(t == tick for t, _ in uses): raise ValueError('Occupied tick is not idle')
        following = [i for t, i in uses if t > tick]
        anchor = following[0] if following else len(c.operations)
        if f.operation != anchor: raise ValueError('Incorrect idle replay anchor')

