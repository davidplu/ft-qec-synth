"""Architecture features and signed stabilizer-preserving basis edits."""
from dataclasses import dataclass, asdict, replace
from hashlib import sha256
import json
from ..architectures.candidate import Candidate
from ..codes.pauli import Pauli
from ..codes.stabilizer import StabilizerCode


@dataclass(frozen=True)
class Design:
    candidate: Candidate
    family: str = 'interval_flag'
    shared_flags: bool = False
    omitted_checks: tuple = ()  # (round, check); never remove mandatory rounds
    omitted_operations: tuple = ()  # stable (round, check, role, interval, position)
    merged_records: tuple = ()  # pairs of deterministic flag channels
    omitted_terminal: tuple = ()  # classical detectors, zero quantum resource cost
    cat_verify: bool = True

    @property
    def id(self):
        return sha256(json.dumps(self.to_dict(), sort_keys=True).encode()).hexdigest()[:20]

    def to_dict(self):
        return {**asdict(self), 'candidate': self.candidate.to_dict()}

    @classmethod
    def from_dict(cls, d):
        return cls(Candidate.from_dict(d['candidate']), d.get('family', 'interval_flag'),
                   d.get('shared_flags', False), tuple(map(tuple, d.get('omitted_checks', []))),
                   tuple(map(tuple, d.get('omitted_operations', []))),
                   tuple(map(tuple, d.get('merged_records', []))),
                   tuple(d.get('omitted_terminal', [])), d.get('cat_verify', True))


def basis_code(original, design):
    code = StabilizerCode.from_dict({'n': original.n, 'generators': design.candidate.generating_basis,
                                    'name': original.name})
    if code.rank != original.rank or code.basis != original.basis:
        # Echelon dictionaries need not share a row representation.
        if code.rank != original.rank or not all(original.is_stabilizer(p) for p in code.generators):
            raise ValueError('Stabilizer module changed')
    # Binary span equality alone does not preserve +1 eigensectors.
    signed = signed_basis(original.generators, original.n)
    for p in code.generators:
        if signed_reduce(p, signed, original.n) != 0:
            raise ValueError('Signed stabilizer group changed')
    design.candidate.validate(code)
    return code


def multiply(a, b):
    """Return canonical unsigned product and its phase i**phase."""
    p = a ^ b
    phase = ((a.x & a.z).bit_count() + (b.x & b.z).bit_count()
             + 2*(a.z & b.x).bit_count() - (p.x & p.z).bit_count()) % 4
    return p, phase


def signed_basis(generators, n):
    rows = {}
    for p in generators:
        x, z, phase = p.x, p.z, (p.x & p.z).bit_count() % 4
        while x or z:
            pivot = (x | z << n).bit_length()-1
            if pivot not in rows:
                rows[pivot] = (x, z, phase)
                break
            bx, bz, bp = rows[pivot]
            phase = (phase + bp + 2*(z & bx).bit_count()) % 4
            x ^= bx; z ^= bz
        else:
            if phase: raise ValueError('Inconsistent signed group')
    return rows


def signed_reduce(p, rows, n, phase=None):
    x, z = p.x, p.z
    phase = (x & z).bit_count() % 4 if phase is None else phase
    while x or z:
        pivot = (x | z << n).bit_length()-1
        if pivot not in rows: return None
        bx, bz, bp = rows[pivot]
        phase = (phase + bp + 2*(z & bx).bit_count()) % 4
        x ^= bx; z ^= bz
    return phase


def basis_mutations(original, design, limit=4):
    code = basis_code(original, design)
    choices = []
    for i, a in enumerate(code.generators):
        for j, b in enumerate(code.generators):
            if i == j: continue
            p, phase = multiply(a, b)
            if phase or not p.weight: continue  # unsigned input format cannot express negative rows
            rows = list(design.candidate.generating_basis); rows[i] = str(p)
            orders = list(design.candidate.orders); orders[i] = tuple(q for q in range(code.n) if (p.x | p.z) >> q & 1)
            flags = list(design.candidate.flag_intervals)
            # Preserve interval count, remap to full new support; no stale endpoints.
            flags[i] = tuple((0, p.weight) for _ in flags[i])
            child = replace(design, candidate=replace(design.candidate, generating_basis=tuple(rows),
                orders=tuple(orders), flag_intervals=tuple(flags)), omitted_operations=(), merged_records=())
            basis_code(original, child)
            choices.append((sum(Pauli.parse(s).weight for s in rows), i, j, child))
    choices.sort(key=lambda x: x[:3])
    return [(d, f'basis_row_{i}_times_{j}') for _, i, j, d in choices[:limit]]
