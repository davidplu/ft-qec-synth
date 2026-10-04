"""Infer all independent stabilizer constraints available in product readout."""
from ..codes.pauli import Pauli
from ..codes.symplectic import nullspace, echelon, reduce_vector


def compatible_products(code, axes):
    if len(axes) != code.n or any(axis not in 'XYZ' for axis in axes):
        raise ValueError('Invalid physical readout axes')
    rows = []
    for q, axis in enumerate(axes):
        mask = 0
        for i, g in enumerate(code.generators):
            x, z = g.x >> q & 1, g.z >> q & 1
            forbidden = x if axis == 'Z' else z if axis == 'X' else x ^ z
            mask |= forbidden << i
        rows.append(mask)
    coefficients = [1 << i for i, g in enumerate(code.generators)
                    if all(p == 'I' or p == axis for p, axis in zip(str(g), axes))]
    coefficients += nullspace(rows, len(code.generators))
    basis = {}; products = []
    for coefficient in coefficients:
        x = z = phase = 0
        indices = []
        for i, g in enumerate(code.generators):
            if coefficient >> i & 1:
                phase = (phase + (g.x & g.z).bit_count() + 2*(z & g.x).bit_count()) % 4
                x ^= g.x; z ^= g.z; indices.append(i)
        p = Pauli(code.n, x, z)
        if not reduce_vector(p.packed, basis): continue
        basis = echelon(list(basis.values()) + [p.packed])
        relative_phase = (phase - (x & z).bit_count()) % 4
        if relative_phase not in (0, 2): raise ArithmeticError('Non-Hermitian commuting product')
        products.append({'check_indices': indices, 'pauli': str(p), 'reference_parity': relative_phase//2})
    return products
