"""Repeated noisy extraction with a physical destructive logical readout."""
from dataclasses import dataclass, asdict, replace
from .model import Circuit
from .extraction import build
from ..codes.logicals import logical_basis
from .readout import compatible_products


@dataclass(frozen=True)
class MemoryConfig:
    rounds: int = 3
    basis: str = 'Z'
    logical_index: int = 0
    noisy_input: bool = False

    def __post_init__(self):
        if self.rounds < 1 or self.basis not in ('X', 'Z') or self.logical_index < 0:
            raise ValueError('Invalid memory configuration')


def build_memory(code, candidate, config=MemoryConfig()):
    base = build(code, candidate)
    pairs = logical_basis(code)
    if pairs and config.logical_index >= len(pairs):
        raise ValueError('Logical index outside encoded dimension')
    logical = pairs[config.logical_index][int(config.basis == 'Z')] if pairs else None
    axes = [p if p != 'I' else config.basis for p in str(logical)] if logical else [config.basis] * code.n
    compatible = [i for i, p in enumerate(code.generators)
                  if all(a == 'I' or a == b for a, b in zip(str(p), axes))]
    products = compatible_products(code, axes)
    c = Circuit(code, base.syndrome_qubits, base.flag_qubits,
                boundary_model='repeated_noisy_memory',
                experiment={**asdict(config), 'logical_pauli': str(logical) if logical else None,
                            'readout_axes': axes, 'final_compatible_checks': compatible,
                            'final_compatible_products': products,
                            'input_boundary': 'ideal_encoded_eigenstate_with_optional_local_preparation_noise'})
    if config.noisy_input:
        for q in range(code.n):
            c.add('IDLE', [q], round_index=-1, role='input_preparation_noise')
    previous = None
    for r in range(config.rounds):
        boundary = c.add('BARRIER', range(c.num_qubits),
                         deps=() if previous is None else (previous,), round_index=r, role='round_start')
        offset = len(c.operations)
        for op in base.operations:
            deps = tuple(offset + d for d in op.deps) + (boundary,)
            c.operations.append(replace(op, deps=deps, round_index=r,
                                        record=f'{op.record}:r{r}' if op.record else None))
        previous = c.add('BARRIER', range(c.num_qubits),
                         deps=tuple(range(offset, len(c.operations))), round_index=r, role='round_end')
        for i in range(len(code.generators)):
            rec = f's{i}:r{r}'
            c.detectors.append([rec] if r == 0 else [f's{i}:r{r-1}', rec])
        c.detectors.extend([[f'{op.record}:r{r}'] for op in base.operations
                            if op.record and op.record.startswith('f')])
    for q, axis in enumerate(axes):
        deps = (previous,)
        if axis == 'Y':
            deps = (c.add('SDG', [q], deps, round_index=config.rounds, role='final_basis_change'),)
        if axis in ('X', 'Y'):
            deps = (c.add('H', [q], deps, round_index=config.rounds, role='final_basis_change'),)
        c.add('M', [q], deps, record=f'd{q}', round_index=config.rounds, role='final_data_readout')
    c.detector_offsets = [0]*len(c.detectors)
    for product in products:
        support = [f'd{q}' for q, p in enumerate(product['pauli']) if p != 'I']
        c.detectors.append([f's{i}:r{config.rounds-1}' for i in product['check_indices']] + support)
        c.detector_offsets.append(product['reference_parity'])
    if logical:
        c.observables.append([f'd{q}' for q, p in enumerate(str(logical)) if p != 'I'])
    c.validate()
    return c
