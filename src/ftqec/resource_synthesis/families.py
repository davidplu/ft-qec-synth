"""Modular extraction families, with real noisy gates and measurements."""
from dataclasses import replace
from typing import Protocol
from ..circuits.model import Circuit
from ..circuits.extraction import build
from ..circuits.gadgets import append_gadget


class ExtractionFamily(Protocol):
    name: str
    def build(self, code, design) -> Circuit: ...


class IntervalFlagFamily:
    name = 'interval_flag'

    def build(self, code, design):
        candidate = design.candidate
        if not design.shared_flags: return build(code, candidate)
        syn = tuple(range(code.n, code.n+candidate.syndrome_budget))
        count = max(map(len, candidate.flag_intervals), default=0)
        flags = tuple(range(code.n+len(syn), code.n+len(syn)+count))
        c = Circuit(code, syn, flags); tails = {}; lanes = {}; flag_tail = None
        for position, i in enumerate(candidate.check_order):
            slot = candidate.ancilla_assignment[i]; lane = position % candidate.parallelism
            uses_flags = bool(candidate.flag_intervals[i])
            deps = tuple(sorted({t for t in (tails.get(slot), lanes.get(lane), flag_tail if uses_flags else None) if t is not None}))
            tail = append_gadget(c, i, candidate.orders[i], candidate.flag_intervals[i], syn[slot], flags, deps)
            tails[slot] = lanes[lane] = tail
            if uses_flags: flag_tail = tail
        c.validate(); return c


class CatStateFamily:
    """Shor-style GHZ controls, retained noisy verification, no postselection."""
    name = 'verified_cat'

    def build(self, code, design):
        a = design.candidate
        # One reusable cat block, serialized checks; real w-qubit footprint.
        width = max(map(len, a.orders), default=1)
        cats = tuple(range(code.n, code.n+width))
        flags = (code.n+width,) if design.cat_verify else ()
        c = Circuit(code, cats, flags); last = ()
        for i in a.check_order:
            order = a.orders[i]; qs = cats[:len(order)]
            def emit(g, qubits, record=None, role=None, interval=None, position=None):
                nonlocal last
                idx = c.add(g, qubits, last, record, i, role=role, interval=interval, interaction_position=position)
                last = (idx,)
            for j,q in enumerate(qs): emit('RESET', [q], role='cat_reset',position=j)
            emit('H', [qs[0]], role='cat_prepare')
            for q in qs[1:]: emit('CX', [qs[0], q], role='cat_entangle')
            if flags:
                for j, q in enumerate(qs[1:]):
                    emit('RESET', flags, role='flag_reset', interval=j)
                    emit('CX', [qs[0], flags[0]], role='cat_verify_open', interval=j)
                    emit('CX', [q, flags[0]], role='cat_verify_close', interval=j)
                    rec = f'f{i}_cat{j}'
                    emit('M', flags, rec, 'flag_readout', j); c.detectors.append([rec])
            text = str(code.generators[i])
            for pos, (anc, q) in enumerate(zip(qs, order)):
                p = text[q]
                if p == 'Y': emit('SDG', [q], role='data_basis_before', position=pos)
                emit('CZ' if p == 'Z' else 'CX', [anc, q], role='data_interaction', position=pos)
                if p == 'Y': emit('S', [q], role='data_basis_after', position=pos)
            for j, q in enumerate(qs):
                emit('H', [q], role='syndrome_basis_readout')
                emit('M', [q], f's{i}_cat{j}', 'syndrome_readout')
        c.validate(); return c


FAMILIES = {f.name: f for f in (IntervalFlagFamily(), CatStateFamily())}


def register_family(family):
    if family.name in FAMILIES: raise ValueError('Family already registered')
    FAMILIES[family.name] = family
