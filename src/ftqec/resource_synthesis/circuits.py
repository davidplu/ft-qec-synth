"""Physical memory circuits with feature edits and ideal-parity validation."""
from dataclasses import asdict, replace
from ..circuits.model import Circuit
from ..circuits.memory import MemoryConfig
from ..circuits.readout import compatible_products
from ..codes.logicals import logical_basis
from ..codes.pauli import Pauli
from ..scheduling.scheduler import schedule
from .design import basis_code, signed_basis, signed_reduce
from .families import FAMILIES


def op_key(op):
    return (op.round_index, op.check, op.role, op.interval, op.interaction_position)


def build_design(original, design, memory=MemoryConfig()):
    code = basis_code(original, design)
    if design.family not in FAMILIES: raise ValueError('Unknown extraction family')
    base = FAMILIES[design.family].build(code, design)
    rounds = memory.rounds + design.candidate.terminal_repetitions
    # Fix the physical observable and terminal axes to the original code.
    pairs = logical_basis(original)
    logical = pairs[memory.logical_index][int(memory.basis == 'Z')] if pairs else None
    axes = [p if p != 'I' else memory.basis for p in str(logical)] if logical else [memory.basis]*code.n
    products = compatible_products(code, axes)
    c = Circuit(code, base.syndrome_qubits, base.flag_qubits, boundary_model='repeated_noisy_memory',
        experiment={**asdict(memory), 'rounds': rounds, 'logical_pauli': str(logical) if logical else None,
            'readout_axes': axes, 'final_compatible_checks': [i for i,p in enumerate(code.generators)
                if all(a == 'I' or a == b for a,b in zip(str(p), axes))],
            'final_compatible_products': products,
            'input_boundary': 'ideal_encoded_eigenstate_with_optional_local_preparation_noise'})
    if memory.noisy_input:
        for q in range(code.n): c.add('IDLE', [q], round_index=-1, role='input_preparation_noise')
    previous = None; last_syndrome = {}; omitted = set(design.omitted_operations)
    for r in range(rounds):
        boundary = c.add('BARRIER', range(c.num_qubits), () if previous is None else (previous,),
                         round_index=r, role='round_start')
        indices = {}; round_records = {}; start = len(c.operations)
        for i, op in enumerate(base.operations):
            fresh = replace(op, round_index=r, record=f'{op.record}:r{r}' if op.record else None)
            deps = {boundary}
            for d in op.deps: deps.update(indices[d])
            if (r, op.check) in design.omitted_checks or op_key(fresh) in omitted:
                indices[i] = deps; continue
            new = replace(fresh, deps=tuple(sorted(deps)))
            idx = len(c.operations); c.operations.append(new); indices[i] = {idx}
            if new.record:
                if new.role == 'syndrome_readout': round_records.setdefault(new.check, []).append(new.record)
                elif new.record.startswith('f'): c.detectors.append([new.record])
        previous = c.add('BARRIER', range(c.num_qubits), tuple(range(start, len(c.operations))),
                         round_index=r, role='round_end')
        # Each measured check is compared to its last actually measured epoch.
        for i, recs in sorted(round_records.items()):
            c.detectors.append(last_syndrome.get(i, []) + recs)
            last_syndrome[i] = recs
    for q, axis in enumerate(axes):
        deps = (previous,)
        if axis == 'Y': deps = (c.add('SDG', [q], deps, round_index=rounds, role='final_basis_change'),)
        if axis in ('X', 'Y'): deps = (c.add('H', [q], deps, round_index=rounds, role='final_basis_change'),)
        c.add('M', [q], deps, record=f'd{q}', round_index=rounds, role='final_data_readout')
    c.detector_offsets = [0]*len(c.detectors)
    for j, product in enumerate(products):
        if j in design.omitted_terminal or any(i not in last_syndrome for i in product['check_indices']): continue
        recs = [rec for i in product['check_indices'] for rec in last_syndrome[i]]
        c.detectors.append(recs + [f'd{q}' for q,p in enumerate(product['pauli']) if p != 'I'])
        c.detector_offsets.append(product['reference_parity'])
    if logical: c.observables.append([f'd{q}' for q,p in enumerate(str(logical)) if p != 'I'])
    for first, second in design.merged_records:
        # Merge information channels, not noisy measurements into ideal checks.
        for r in range(rounds):
            a, b = [f'{name}:r{r}' for name in (first, second)]
            ia = next((i for i,d in enumerate(c.detectors) if d == [a]), None)
            ib = next((i for i,d in enumerate(c.detectors) if d == [b]), None)
            if ia is not None and ib is not None:
                c.detectors[ia] = [a,b]; c.detectors.pop(ib); c.detector_offsets.pop(ib)
    # Remove physically unused ancillas and compact addresses after omissions.
    used = set(range(code.n)) | {q for op in c.operations if op.gate != 'BARRIER' for q in op.qubits}
    remap = {q:i for i,q in enumerate(sorted(used))}
    c.syndrome_qubits = tuple(remap[q] for q in c.syndrome_qubits if q in used)
    c.flag_qubits = tuple(remap[q] for q in c.flag_qubits if q in used)
    c.operations = [replace(op, qubits=tuple(range(len(used))) if op.gate == 'BARRIER'
                           else tuple(remap[q] for q in op.qubits)) for op in c.operations]
    c.validate(); schedule(c)  # always a fresh schedule, never reuse parent's depth
    return c


def ideal_parity(circuit, records):
    """Signed Heisenberg parity propagation through Clifford measurement/reset.

    Reject parities that depend on an intrinsically random measurement. The
    initial state is the code's +1 sector and the chosen +1 logical eigenstate.
    This is essential when deleting half a flag pair or an ancilla reset.
    """
    selected = set(records); x = z = phase = 0
    def h(q):
        nonlocal x,z,phase
        a = x >> q & 1; b = z >> q & 1
        phase = (phase+2*a*b) % 4
        if a != b: x ^= 1 << q; z ^= 1 << q
    for op in reversed(circuit.operations):
        gate = op.gate
        if gate == 'BARRIER': continue
        q = op.qubits[0]; mask = 1 << q
        if gate == 'M':
            if x & mask: return None
            if op.record in selected: z ^= mask
        elif gate in ('RESET', 'PREP'):
            if x & mask: return None
            z &= ~mask
        elif gate == 'H': h(q)
        elif gate in ('S', 'SDG'):
            if x & mask:
                phase = (phase + (3 if gate == 'S' else 1)) % 4
                z ^= mask
        elif gate in ('CX', 'CZ'):
            b = op.qubits[1]
            if gate == 'CZ': h(b)
            if x & mask: x ^= 1 << b
            if z >> b & 1: z ^= mask
            if gate == 'CZ': h(b)
        elif gate == 'SWAP':
            b = op.qubits[1]
            if (x >> q ^ x >> b) & 1: x ^= mask | 1 << b
            if (z >> q ^ z >> b) & 1: z ^= mask | 1 << b
        elif gate in ('X','Y','Z'):
            anti = (bool(z & mask) if gate == 'X' else bool(x & mask) if gate == 'Z' else bool((x ^ z) & mask))
            phase = (phase + 2*anti) % 4
    # Ancillas start in |0>; an unreset X factor is not deterministic.
    data_mask = (1 << circuit.code.n)-1
    if x & ~data_mask: return None
    x &= data_mask; z &= data_mask
    gens = list(circuit.code.generators)
    logical = circuit.experiment.get('logical_pauli')
    if logical: gens.append(Pauli.parse(logical))
    sign = signed_reduce(Pauli(circuit.code.n, x,z), signed_basis(gens, circuit.code.n), circuit.code.n, phase)
    return None if sign not in (0,2) else sign//2


def validate_ideal(circuit):
    offsets = circuit.detector_offsets or [0]*len(circuit.detectors)
    for i, (row, expected) in enumerate(zip(circuit.detectors, offsets)):
        if ideal_parity(circuit, row) != expected:
            return {'verified': False, 'invalid_detector': i}
    for i, row in enumerate(circuit.observables):
        if ideal_parity(circuit, row) != 0:
            return {'verified': False, 'invalid_observable': i}
    return {'verified': True, 'method': 'signed_heisenberg_measurement_parity'}
