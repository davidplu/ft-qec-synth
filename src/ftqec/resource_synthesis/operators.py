"""Explicit single-feature compressions; all proposals require recertification."""
from dataclasses import replace
from .circuits import op_key


def compressions(design, circuit, mandatory_rounds=3):
    a = design.candidate; proposals = []
    def offer(child, operator, feature):
        if child.id != design.id: proposals.append((child,operator,feature))
    # Expensive checks first, then stable IDs; no code-specific priorities.
    costs = {i:sum(op.gate in ('CX','CZ') for op in circuit.operations if op.check == i) for i in range(len(a.orders))}
    for i in sorted(costs,key=lambda i:(-costs[i],i)):
        fs = a.flag_intervals[i]
        if design.family == 'interval_flag':
            for j, interval in enumerate(fs):
                flags = list(a.flag_intervals); flags[i] = fs[:j]+fs[j+1:]
                offer(replace(design,candidate=replace(a,flag_intervals=tuple(flags))), 'remove_flag_ancilla', f'flag:{i}:{j}')
            for j in range(len(fs)-1):
                merged = (min(fs[j][0],fs[j+1][0]),max(fs[j][1],fs[j+1][1]))
                flags = list(a.flag_intervals); flags[i] = fs[:j]+(merged,)+fs[j+2:]
                offer(replace(design,candidate=replace(a,flag_intervals=tuple(flags))), 'merge_flag_intervals', f'interval_pair:{i}:{j}')
                offer(replace(design,merged_records=design.merged_records+((f'f{i}_{j}',f'f{i}_{j+1}'),)),
                      'merge_flag_records', f'flag_records:{i}:{j}')
        order = tuple(sorted(a.orders[i]))
        if order != a.orders[i]:
            orders = list(a.orders); orders[i] = order
            offer(replace(design,candidate=replace(a,orders=tuple(orders))), 'simplify_interaction_order', f'order:{i}')
    if a.syndrome_budget > 1 and design.family == 'interval_flag':
        # One slot merge at a time, preserving all other assignments.
        for slot in range(1,a.syndrome_budget):
            assignment = tuple(0 if q == slot else q-1 if q > slot else q for q in a.ancilla_assignment)
            child = replace(a,syndrome_budget=a.syndrome_budget-1,ancilla_assignment=assignment,
                            parallelism=min(a.parallelism,a.syndrome_budget-1))
            offer(replace(design,candidate=child), 'reuse_syndrome_ancilla', f'syndrome_slot:{slot}')
    if not design.shared_flags and design.family == 'interval_flag':
        offer(replace(design,shared_flags=True), 'reuse_flag_ancilla', 'global_flag_pool')
    if a.parallelism < a.syndrome_budget and design.family == 'interval_flag':
        offer(replace(design,candidate=replace(a,parallelism=a.syndrome_budget)), 'increase_safe_parallelism', 'lane_serialization')
    if a.terminal_repetitions:
        offer(replace(design,candidate=replace(a,terminal_repetitions=0)), 'remove_redundant_terminal_round', 'extra_terminal_round')
    if design.family == 'verified_cat' and design.cat_verify:
        offer(replace(design,cat_verify=False), 'remove_cat_verification', 'cat_verification')
    for r in range(mandatory_rounds+a.terminal_repetitions):
        for i in sorted(costs,key=lambda i:(-costs[i],i)):
            if (r,i) not in design.omitted_checks and sum((rr,i) not in design.omitted_checks
                    for rr in range(mandatory_rounds+a.terminal_repetitions))>1:
                offer(replace(design,omitted_checks=design.omitted_checks+((r,i),)),
                      'remove_redundant_syndrome_measurement', f'check_epoch:{r}:{i}')
    for op in circuit.operations:
        key = op_key(op)
        if key in design.omitted_operations: continue
        if op.role in ('flag_open','flag_close'):
            offer(replace(design,omitted_operations=design.omitted_operations+(key,)),
                  'remove_one_flag_interaction', f'operation:{key}')
        if op.gate == 'RESET' and op.round_index is not None and op.round_index > 0:
            offer(replace(design,omitted_operations=design.omitted_operations+(key,)),
                  'reduce_reset_measurement_cycles', f'operation:{key}')
    for j in range(len(circuit.experiment['final_compatible_products'])):
        if j not in design.omitted_terminal:
            offer(replace(design,omitted_terminal=design.omitted_terminal+(j,)),
                  'remove_redundant_terminal_verification', f'terminal_detector:{j}')
    unique = {}
    for child,op,feature in proposals: unique.setdefault((child.id,op,feature),(child,op,feature))
    return list(unique.values())


OPERATOR_ALIASES = {
    'reduce_independent_flag_intervals':'remove_flag_ancilla',
    'shorten_measurement_sequence':'remove_redundant_syndrome_measurement',
    'reduce_unnecessary_serialization':'increase_safe_parallelism',
    'reduce_duplicated_fault_information_channels':'merge_flag_intervals',
}
