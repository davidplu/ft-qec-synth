def beam_order(record):
    """Deterministic lexicographic tie-break for finite beam allocation only."""
    r=record['resources']
    return (-record['bounds']['lower_bound'],r['QD'],r['two_q_gates'],record['architecture_id'])
