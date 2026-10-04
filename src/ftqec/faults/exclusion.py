"""Independent exclusion audit using physical boolean replay per singleton.

No suffix signatures, spectrum classes or certificate engine are consumed.
All distinct-location fault combinations through the claimed excluded weight
are checked with a separately implemented detector join.
"""
from collections import defaultdict
from itertools import combinations
from .signatures import enumerate_faults
from .batch_verification import singleton_effects


def verify_exclusion(circuit, through, idles=False):
    if not 0 <= through <= 3: raise ValueError('Independent exclusion supports weights zero through three')
    faults = list(enumerate_faults(circuit, idles))
    effects = singleton_effects(circuit, faults)
    for i, (d,l) in enumerate(effects):
        if through >= 1 and not d and l: return {'verified': False, 'counterexample_indices': [i]}
    groups = defaultdict(list)
    for i,(d,l) in enumerate(effects): groups[d].append(i)
    inspected = len(faults) if through else 0
    if through >= 2:
        for indices in groups.values():
            for i,j in combinations(indices, 2):
                if faults[i].location == faults[j].location: continue
                inspected += 1
                if effects[i][1] ^ effects[j][1]: return {'verified': False, 'counterexample_indices': [i,j]}
    if through >= 3:
        for k, (d,l) in enumerate(effects):
            for i in range(k):
                for j in groups.get(d ^ effects[i][0], []):
                    if not i < j < k: continue
                    if len({faults[x].location for x in (i,j,k)}) != 3: continue
                    inspected += 1
                    if l ^ effects[i][1] ^ effects[j][1]: return {'verified': False, 'counterexample_indices': [i,j,k]}
    return {'verified': True, 'excluded_through': through, 'singleton_replay_count': len(faults),
            'joined_combinations_checked': inspected, 'method': 'bit_lane_boolean_replay_singletons_independent_detector_join'}
