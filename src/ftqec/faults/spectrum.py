"""Complete bounded malignant layers; capped observations never become counts."""
from collections import defaultdict
from dataclasses import dataclass
from hashlib import sha256
from itertools import combinations
import json
from .search import witness
from ..codes.pauli import Pauli


@dataclass(frozen=True)
class MalignantFaultClass:
    weight: int
    detector_signature: int
    logical_effect: int
    fault_mechanisms: tuple
    hook_support: tuple
    flag_outcomes: tuple

    @property
    def key(self):
        return json.dumps(self.__dict__, sort_keys=True, separators=(',', ':'))

    @property
    def id(self):
        return sha256(self.key.encode()).hexdigest()[:24]


def fault_features(circuit, signature):
    f = signature.fault
    p = Pauli.unpack(circuit.code.n, signature.data)
    support = tuple(q for q in range(p.n) if (p.x | p.z) >> q & 1)
    op = circuit.operations[f.operation] if f.operation < len(circuit.operations) else None
    # Include exact data support, but omit disposable ancilla numbering and Pauli
    # labels when their observable mechanism agrees. No permutation of checks,
    # rounds, data qubits, or interaction positions is allowed.
    flag_names = sorted(o.record for o in circuit.operations if o.record and o.record.startswith('f'))
    flags = tuple(name for i, name in enumerate(flag_names) if signature.flags >> i & 1)
    data_targets = tuple(q for q in f.qubits if q < circuit.code.n)
    detector_rows = tuple(tuple(sorted(row)) for i, row in enumerate(circuit.detectors)
                          if signature.detectors >> i & 1)
    return (f.round_index, f.check, op.gate if op else 'IDLE', f.kind,
            f.role, f.interval, f.interaction_position, data_targets,
            support if p.weight > 1 else (), flags, detector_rows,
            signature.logical, p.packed), support, flags


def classify(circuit, group, features=None):
    features = features or {id(s): fault_features(circuit, s) for s in group}
    detector = logical = flags = 0; hooks = set(); fs = []
    for s in group:
        detector ^= s.detectors; logical ^= s.logical; flags ^= s.flags
        mechanism, support, named_flags = features[id(s)]
        fs.append(mechanism)
        if len(support) > 1: hooks.update(support)
    return MalignantFaultClass(len(group), detector, logical,
        tuple(sorted(fs, key=lambda x: json.dumps(x))), tuple(sorted(hooks)), (flags,))


def cancelling_groups(ss, weight, work):
    """Unique increasing-index realizations at distinct physical locations.

    Pair/triple detector matching is exhaustive because any undetected set has
    XOR zero. Work counts inspected candidates, including unmatched triple pairs.
    """
    groups = defaultdict(list)
    for i, s in enumerate(ss): groups[s.detectors].append(i)
    if weight == 1:
        for i, s in enumerate(ss):
            work()
            if not s.detectors: yield (i,)
    elif weight == 2:
        for indices in groups.values():
            for i, j in combinations(indices, 2):
                work()
                if ss[i].fault.location != ss[j].fault.location: yield (i, j)
    elif weight == 3:
        for i, a in enumerate(ss):
            for j in range(i+1, len(ss)):
                work()
                b = ss[j]
                if a.fault.location == b.fault.location: continue
                for k in groups.get(a.detectors ^ b.detectors, ()):
                    if k <= j: continue
                    work()
                    if ss[k].fault.location not in (a.fault.location, b.fault.location): yield (i, j, k)
    else:
        for indices in combinations(range(len(ss)), weight):
            work()
            if len({ss[i].fault.location for i in indices}) != weight: continue
            d = 0
            for i in indices: d ^= ss[i].detectors
            if not d: yield indices


class WorkLimit(Exception):
    pass


def malignant_spectrum(circuit, ss, max_weight=3, max_work=200000):
    if not 1 <= max_weight <= 6 or max_work < 0: raise ValueError('Invalid spectrum limits')
    used = 0; layers = {}; classes = {}; members = {}; features = {id(s): fault_features(circuit, s) for s in ss}
    def work():
        nonlocal used
        if used >= max_work: raise WorkLimit()
        used += 1
    for weight in range(1, max_weight+1):
        raw = 0; structural = {}; signature_keys = set(); hooks = set(); logicals = set(); complete = True
        try:
            for indices in cancelling_groups(ss, weight, work):
                group = [ss[i] for i in indices]; logical = 0
                for s in group: logical ^= s.logical
                if not logical: continue
                raw += 1; cls = classify(circuit, group, features); cid = cls.id
                structural[cid] = structural.get(cid, 0)+1
                classes.setdefault(cid, {'id': cid, 'weight': weight, 'logical_effect': logical,
                    'hook_support': list(cls.hook_support), 'mechanisms': cls.fault_mechanisms,
                    'representative_indices': indices})
                members.setdefault(cid, []).append(indices)
                signature_keys.add((0, logical)); hooks.add(cls.hook_support); logicals.add(logical)
        except WorkLimit: complete = False
        layers[str(weight)] = {'complete': complete,
            'class_count': len(structural) if complete else None,
            'raw_count': raw if complete else None,
            'signature_count': len(signature_keys) if complete else None,
            'observed_class_count': len(structural), 'observed_raw_count': raw,
            'logical_effect_diversity': len(logicals), 'hook_support_diversity': len(hooks),
            'multiplicities': structural}
        # The first nonzero layer is the frontier. Higher layers are explicitly
        # unknown; they cannot improve distance or serve as exact objectives.
        if raw or not complete: break
    for weight in range(1, max_weight+1):
        layers.setdefault(str(weight), {'complete': False, 'class_count': None,
            'raw_count': None, 'signature_count': None, 'reason': 'not_searched_above_frontier'})
    return {'layers': layers, 'work': used, 'classes': list(classes.values())}, members


def representative_witness(circuit, ss, cls):
    return witness(circuit, [ss[i] for i in cls['representative_indices']]).to_dict()


def spectrum_delta(parent, child):
    return {w: (child['layers'][w]['class_count']-p['class_count']
        if p['complete'] and child['layers'][w]['complete'] else None)
        for w, p in parent['layers'].items()}


def boundary_class(w):
    roles = {f.get('role') for f in w['faults']}
    if roles <= {'final_data_readout', 'final_basis_change'}:
        return 'BOUNDARY_READOUT_FAILURE', 'UNSUPPORTED_REPAIR_CLASS'
    if roles & {'final_data_readout', 'final_basis_change'}:
        return 'BOUNDARY_READOUT_FAILURE', 'TERMINAL_VERIFICATION_CANDIDATE'
    return 'EXTRACTION_FAILURE', 'SUPPORTED_GENERIC_REPAIR'
