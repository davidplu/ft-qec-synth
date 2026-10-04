"""Deterministic counterexample features and portable fault addresses."""
from dataclasses import dataclass, asdict
from hashlib import sha256
import json
from ..codes.pauli import Pauli
from ..scheduling.scheduler import schedule


@dataclass(frozen=True)
class CounterexampleAnalysis:
    counterexample_id: str
    total_fault_weight: int
    rounds: list
    checks: list
    round_relation: str
    check_relation: str
    data_hook_support: list
    hook_weight: int
    implicated_intervals: list
    flag_records_triggered: list
    flag_records_cancelled: list
    measurement_faults: int
    reset_faults: int
    idle_faults: int
    shared_gadget: bool
    independent_completion: bool
    overlapping_gadgets: bool
    failure_classes: list

    def to_dict(self): return asdict(self)


def analyze(circuit, witness, signatures):
    index = {(s.fault.location, s.fault.label): s for s in signatures}
    group = [index[(f['location'], f['label'])] for f in witness['faults']]
    rounds = sorted({s.fault.round_index for s in group if s.fault.round_index is not None})
    checks = sorted({s.fault.check for s in group if s.fault.check is not None})
    gadgets = [(s.fault.round_index, s.fault.check) for s in group if s.fault.check is not None]
    hook = set(); intervals = []
    for s in group:
        f = s.fault
        p = Pauli.unpack(circuit.code.n, s.data)
        support = [q for q in range(p.n) if (p.x | p.z) >> q & 1]
        if p.weight > 1: hook.update(support)
        if f.interaction_position is not None:
            intervals.append(dict(round=f.round_index, check=f.check, flag_interval=f.interval,
                                  interaction_position=f.interaction_position, propagated_support=support))
    names = sorted(op.record for op in circuit.operations if op.record and op.record.startswith('f'))
    triggered = []; cancelled = []
    for i, name in enumerate(names):
        count = sum(s.flags >> i & 1 for s in group)
        if count: triggered.append(name)
        if count and count % 2 == 0: cancelled.append(name)
    sched = schedule(circuit); spans = {}
    for i, op in enumerate(circuit.operations):
        if op.check is not None:
            key = (op.round_index, op.check)
            lo, hi = spans.get(key, (sched.starts[i], sched.starts[i]+1))
            spans[key] = (min(lo, sched.starts[i]), max(hi, sched.starts[i]+1))
    overlap = any(a != b and a in spans and b in spans and
                  max(spans[a][0], spans[b][0]) < min(spans[a][1], spans[b][1])
                  for a in gadgets for b in gadgets)
    classes = []
    if hook: classes.append('SAME_CHECK_HOOK' if len(checks) == 1 else 'INTERACTION_ORDER_HOOK')
    if cancelled: classes.append('FLAG_CANCELLATION')
    if any(s.fault.kind == 'measurement' and s.fault.role == 'flag_readout' for s in group):
        classes.append('FLAG_READOUT_HIDING')
    if len(checks) > 1: classes.append('CROSS_CHECK_OVERLAP' if overlap else 'CROSS_CHECK_COLLISION')
    if any(s.fault.role == 'final_data_readout' for s in group): classes.append('FINAL_READOUT')
    if not classes: classes.append('OTHER')
    identifier = sha256(json.dumps(witness, sort_keys=True).encode()).hexdigest()[:20]
    return CounterexampleAnalysis(identifier, len(group), rounds, checks,
        'same-round' if len(rounds) == 1 else 'cross-round',
        'same-check' if len(checks) == 1 else 'cross-check' if checks else 'unassigned',
        sorted(hook), len(hook), intervals, triggered, cancelled,
        sum(s.fault.kind == 'measurement' for s in group),
        sum(s.fault.kind in ('reset', 'preparation', 'prep') for s in group),
        sum(s.fault.kind == 'idle' for s in group), len(gadgets) != len(set(gadgets)),
        bool(hook) and any(Pauli.unpack(circuit.code.n,s.data).weight == 1 for s in group), overlap, classes)


def semantic_address(circuit, operation):
    op = circuit.operations[operation]
    data = tuple(q for q in op.qubits if q < circuit.code.n)
    return op.round_index, op.check, op.gate, op.role, op.interval, data


def transport_witness(parent, child, witness):
    """Map the same local gate fault to a unique semantic child location.

    Idle tick remapping and removed/ambiguous locations are explicitly unresolved.
    No witness elimination credit is given just because indices changed.
    """
    addresses = {}
    for i in range(len(child.operations)):
        addresses.setdefault(semantic_address(child, i), []).append(i)
    mapped = []
    for fault in witness['faults']:
        if fault['kind'] == 'idle' or fault['operation'] >= len(parent.operations):
            return None, 'idle_or_boundary_address_not_transportable'
        options = addresses.get(semantic_address(parent, fault['operation']), [])
        if len(options) != 1: return None, 'removed_or_ambiguous_semantic_location'
        i = options[0]; op = child.operations[i]
        mapped.append({**fault, 'operation': i, 'qubits': list(op.qubits), 'location': f'op:{i}',
                       'round_index': op.round_index, 'check': op.check, 'role': op.role,
                       'interval': op.interval, 'interaction_position': op.interaction_position})
    if len({f['location'] for f in mapped}) != len(mapped): return None, 'merged_physical_locations'
    return mapped, None
