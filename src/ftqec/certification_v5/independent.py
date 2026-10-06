"""Structurally separate physical-location trellis, using Boolean forward replay.

Process each location once, selecting no fault or one legal physical variant.
For a given accumulated syndrome/logical state, only minimum weight is needed:
future choices use disjoint locations. A state cap is always inconclusive.
"""
from collections import defaultdict
import time
from ..faults.signatures import enumerate_faults
from ..faults.batch_verification import singleton_effects


def exclusion(circuit,through,state_limit=250000,work_limit=2000000):
    if through<0: raise ValueError('Negative exclusion weight')
    started=time.perf_counter(); faults=list(enumerate_faults(circuit,False))
    effects=singleton_effects(circuit,faults); locations=defaultdict(set)
    for f,e in zip(faults,effects): locations[f.location].add(tuple(e))
    nd=len(circuit.detectors); states={0:0}; work=0; peak=1
    for location in sorted(locations):
        updated=dict(states)
        for state,weight in states.items():
            if weight>=through: continue
            for d,l in locations[location]:
                if work>=work_limit:
                    return dict(verified=False,reason='work_limit',work=work,peak_states=peak)
                work+=1; key=state ^ d ^ (l << nd)
                if weight+1<updated.get(key,through+1): updated[key]=weight+1
                if len(updated)>state_limit:
                    return dict(verified=False,reason='state_limit',work=work,peak_states=len(updated))
        states=updated; peak=max(peak,len(states))
    violations=[w for state,w in states.items() if not (state&((1<<nd)-1)) and (state>>nd)]
    return dict(verified=not violations,excluded_through=through if not violations else None,
                violating_weight=min(violations,default=None),work=work,peak_states=peak,
                runtime_seconds=time.perf_counter()-started,algorithm='physical-location-forward-trellis-1')
