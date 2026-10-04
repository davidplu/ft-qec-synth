"""Generic counterexample, resource, and random mutation proposals."""
from dataclasses import dataclass, replace, asdict
from .mutations import mutate


@dataclass(frozen=True)
class Provenance:
    kind: str
    parent_id: str | None = None
    source_counterexample_id: str | None = None
    failure_class: str | None = None
    repair_operator: str | None = None

    def to_dict(self): return asdict(self)


def targeted_repairs(candidate, analysis, rng, max_flags=4):
    proposals = []
    failure = analysis.failure_classes[0]
    def offer(child, operator, cls=failure):
        if child.id != candidate.id:
            proposals.append((child, Provenance('COUNTEREXAMPLE_GUIDED', candidate.id,
                analysis.counterexample_id, cls, operator)))
    for check in analysis.checks:
        order = candidate.orders[check]; width = len(order)
        if width < 2: continue
        implicated = [j for j,q in enumerate(order) if q in analysis.data_hook_support]
        pivot = max(1, min(width-1, min(implicated) if implicated else width//2))
        for interval, name in [((0,width),'independent_full_interval_flag'),
                               ((0,pivot),'split_prefix_flag'), ((pivot,width),'split_suffix_flag')]:
            flags = [list(f) for f in candidate.flag_intervals]
            if len(flags[check]) < max_flags:
                flags[check].append(interval)
                cls = 'FLAG_READOUT_HIDING' if 'FLAG_READOUT_HIDING' in analysis.failure_classes else 'FLAG_CANCELLATION' if analysis.flag_records_cancelled else failure
                offer(replace(candidate,flag_intervals=tuple(tuple(f) for f in flags)), name, cls)
        if candidate.flag_intervals[check]:
            flags = [list(f) for f in candidate.flag_intervals]
            flags[check][0]=(0,pivot)
            if len(flags[check]) < max_flags: flags[check].append((pivot,width))
            offer(replace(candidate,flag_intervals=tuple(tuple(f) for f in flags)), 'split_temporal_flag_records')
        separated = tuple(q for q in order if q not in analysis.data_hook_support) + tuple(q for q in order if q in analysis.data_hook_support)
        orders = list(candidate.orders); orders[check] = separated
        offer(replace(candidate,orders=tuple(orders)), 'redirect_hook_order')
        orders = list(candidate.orders); orders[check] = tuple(reversed(order))
        offer(replace(candidate,orders=tuple(orders)), 'reverse_implicated_order')
        for pos in implicated:
            dest = rng.randrange(width)
            reordered = list(order); reordered[pos], reordered[dest] = reordered[dest], reordered[pos]
            orders = list(candidate.orders); orders[check] = tuple(reordered)
            offer(replace(candidate,orders=tuple(orders)), 'separate_hook_support')
    if len(analysis.checks) > 1:
        offer(replace(candidate,parallelism=1), 'serialize_cross_check_gadgets', 'CROSS_CHECK_COLLISION')
        count = len(candidate.orders)
        offer(replace(candidate,syndrome_budget=max(1,count),ancilla_assignment=tuple(range(count))),
              'separate_syndrome_ancillas', 'CROSS_CHECK_COLLISION')
        order = tuple(i for i in candidate.check_order if i not in analysis.checks) + tuple(analysis.checks)
        offer(replace(candidate,check_order=order), 'change_implicated_check_order', 'CROSS_CHECK_COLLISION')
    unique = {}
    for child, provenance in proposals: unique.setdefault(child.id, (child, provenance))
    return list(unique.values())


def random_proposal(candidate, rng):
    return mutate(candidate, rng, max_flags=4), Provenance('RANDOM', candidate.id, repair_operator='random_local_mutation')


def resource_proposal(candidate, rng):
    action = rng.randrange(4)
    if action == 0:
        budget = max(1, candidate.syndrome_budget-1)
        child = replace(candidate,syndrome_budget=budget,parallelism=min(candidate.parallelism,budget),
                        ancilla_assignment=tuple(a % budget for a in candidate.ancilla_assignment))
        operator = 'reduce_syndrome_budget'
    elif action == 1:
        flags = [list(f) for f in candidate.flag_intervals]
        choices = [i for i,f in enumerate(flags) if f]
        if choices: flags[rng.choice(choices)].pop()
        child = replace(candidate,flag_intervals=tuple(tuple(f) for f in flags)); operator = 'remove_flag_resource'
    elif action == 2:
        child = replace(candidate,parallelism=candidate.syndrome_budget); operator = 'maximize_parallelism'
    else:
        order=list(candidate.check_order); rng.shuffle(order)
        child=replace(candidate,check_order=tuple(order)); operator='reorder_for_resources'
    return child, Provenance('RESOURCE_GUIDED',candidate.id,repair_operator=operator)
