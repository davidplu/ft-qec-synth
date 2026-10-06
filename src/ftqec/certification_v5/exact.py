"""Location-compatible meet-in-the-middle distance exclusions.

A minimum malignant set contains neither a zero (detector, logical) signature
nor two equal signatures: deleting these preserves its nonzero logical XOR.
Thus minimum distance can be searched using distinct signature types, retaining
ALL physical locations per type. Bipartite matching supplies legal realizations.
Completed lower weights justify exclusion of nonminimal sets at higher weights.
"""
from collections import defaultdict
from itertools import combinations
from hashlib import sha256
import json, time
from ..faults.search import witness
from ..faults.verification import verify_witness
from ..resource_synthesis.certification import fingerprint

VERSION = 'location-compatible-mitm-1'
FAULT_MODEL = 'operation-local Pauli faults; measurement flips; no idles; one variant per location'


def canonical_types(signatures):
    groups = defaultdict(dict)
    for s in signatures:
        if s.detectors or s.logical:
            groups[(s.detectors, s.logical)].setdefault(s.fault.location, s)
    return [(key, groups[key]) for key in sorted(groups)]


def realization(types, indices):
    """Exact augmenting-path matching; each returned fault has a distinct location."""
    assigned = {}
    def augment(index, seen):
        for location in sorted(types[index][1]):
            if location in seen: continue
            seen.add(location)
            if location not in assigned or augment(assigned[location], seen):
                assigned[location] = index
                return True
        return False
    for i in sorted(indices, key=lambda j: len(types[j][1])):
        if not augment(i, set()): return None
    return [types[i][1][loc] for loc, i in sorted(assigned.items())]


def certify(circuit, signatures, target, work_limit=1000000, table_limit=250000):
    if target < 2 or work_limit < 0 or table_limit < 1: raise ValueError('Invalid certification limits')
    started = time.perf_counter(); types = canonical_types(signatures)
    work = 0; completed = 0; upper = None; found = None; reason = None
    profile = dict(table_entries_peak=0, location_checks=0, join_checks=0, subset_checks=0)
    class Stop(Exception): pass
    def spend(kind):
        nonlocal work, reason
        if work >= work_limit: reason = 'work_limit'; raise Stop
        work += 1; profile[kind] += 1
    def subsets(size):
        for ids in combinations(range(len(types)), size):
            spend('subset_checks'); d = l = 0
            for i in ids: d ^= types[i][0][0]; l ^= types[i][0][1]
            yield ids, d, l
    try:
        for weight in range(1, target):
            left_size = weight // 2; right_size = weight - left_size
            table = defaultdict(list); entries = 0
            for ids, d, l in subsets(left_size):
                if entries >= table_limit: reason = 'table_limit'; raise Stop
                table[d].append((ids, l)); entries += 1
            profile['table_entries_peak'] = max(profile['table_entries_peak'], entries)
            for right, d, l in subsets(right_size):
                for left, ll in table.get(d, ()):
                    spend('join_checks')
                    if not (l ^ ll) or set(left).intersection(right): continue
                    spend('location_checks'); selected = realization(types, left + right)
                    if selected is None: continue
                    found = witness(circuit, selected).to_dict(); upper = weight
                    if not verify_witness(circuit.to_dict(), found)['verified']:
                        raise ArithmeticError('MITM witness failed physical replay')
                    break
                if found: break
            if found: break
            completed = weight
    except Stop: pass
    inventory = [s.fault.to_dict() for s in signatures]
    inventory_hash = sha256(json.dumps(inventory, sort_keys=True).encode()).hexdigest()
    return dict(status='EXACT' if upper == completed + 1 else 'UPPER_BOUND' if upper else
                'LOWER_BOUND' if completed else 'UNKNOWN', lower_bound=completed + 1,
                upper_bound=upper, excluded_through=completed, witness=found,
                reason=reason, combinations_examined=work, requested_weight=target-1,
                fault_locations=len({s.fault.location for s in signatures}), fault_variants=len(signatures),
                signature_types=len(types), runtime_seconds=time.perf_counter()-started, profile=profile,
                certificate=dict(circuit_hash=fingerprint(circuit), fault_model_hash=sha256(FAULT_MODEL.encode()).hexdigest(),
                    fault_inventory_hash=inventory_hash, target=target, algorithm_version=VERSION,
                    work_limit=work_limit, table_limit=table_limit, payload={'excluded_through':completed,
                    'proof':'minimum sets have distinct nonzero types; complete XOR joins; exact location matching'}))
