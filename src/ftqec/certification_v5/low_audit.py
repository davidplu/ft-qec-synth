"""Independent forward physical replay with an exhaustive logical-group pair test."""
from collections import defaultdict
from itertools import combinations
from ..faults.signatures import enumerate_faults
from ..faults.batch_verification import singleton_effects
from ..faults.exclusion import verify_exclusion
from ..faults.verification import verify_witness


def exclude(circuit,through):
    if through>2:return verify_exclusion(circuit,through)
    faults=list(enumerate_faults(circuit,False));effects=singleton_effects(circuit,faults)
    groups=defaultdict(lambda:defaultdict(dict))
    for i,(d,l) in enumerate(effects):
        if through>=1 and not d and l:return dict(verified=False,counterexample_indices=[i])
        groups[d][l].setdefault(faults[i].location,i)
    work=0
    if through>=2:
        for logicals in groups.values():
            # Same-logical pairs cancel logically and can never be malignant.
            for a,b in combinations(logicals,2):
                left,right=logicals[a],logicals[b];work+=1
                for loc,i in left.items():
                    for other,j in right.items():
                        if loc!=other:return dict(verified=False,counterexample_indices=[i,j])
                        # If one group has another location, a distinct pair exists.
                    if len(right)>1:break
    return dict(verified=True,excluded_through=through,singleton_replay_count=len(faults),
                logical_group_pairs=work,method='independent_forward_physical_logical_group_pairs')


def audit(record,circuit,target):
    through=min(target-1,record['bounds']['lower_bound']-1)
    result=exclude(circuit,through)
    if record['bounds'].get('witness'):
        result['witness']=verify_witness(circuit.to_dict(),record['bounds']['witness'])
        result['verified'] &= result['witness']['verified']
    return result
