"""Optional independent integer SAT check over every physical fault variant."""
from collections import defaultdict
from hashlib import sha256
import json,time
from ..faults.signatures import enumerate_faults
from ..faults.batch_verification import singleton_effects
from ..faults.verification import replay,verify_witness
from ..resource_synthesis.certification import fingerprint


def exclusion(circuit,through,seconds=60,deterministic_time=30,model_path=None):
    if through<0 or seconds<0 or deterministic_time<0:raise ValueError('Negative verification limit')
    import ortools
    from ortools.sat.python import cp_model
    started=time.perf_counter();faults=list(enumerate_faults(circuit,False))
    effects=singleton_effects(circuit,faults);forward=time.perf_counter()
    model=cp_model.CpModel();variables=[model.new_bool_var(f'f{i}') for i in range(len(faults))]
    locations=defaultdict(list)
    for i,f in enumerate(faults):locations[f.location].append(variables[i])
    for choices in locations.values():model.add_at_most_one(choices)
    for bit in range(len(circuit.detectors)):
        model.add_bool_xor([variables[i] for i,(d,l) in enumerate(effects) if d>>bit&1]+[True])
    logical=[]
    for bit in range(max((l.bit_length() for d,l in effects),default=0)):
        value=model.new_bool_var(f'logical_{bit}');logical.append(value)
        model.add_bool_xor([variables[i] for i,(d,l) in enumerate(effects) if l>>bit&1]+[value.Not()])
    model.add_bool_or(logical);model.add(sum(variables)<=through)
    if model_path:model.export_to_file(str(model_path))
    solver=cp_model.CpSolver();solver.parameters.max_time_in_seconds=seconds
    solver.parameters.max_deterministic_time=deterministic_time
    solver.parameters.num_search_workers=1;solver.parameters.random_seed=0
    built=time.perf_counter();status=solver.solve(model)
    result=dict(verified=status==cp_model.INFEASIBLE,status=solver.status_name(status),
        excluded_through=through if status==cp_model.INFEASIBLE else None,
        solver_version=ortools.__version__,algorithm='physical-variant-forward-xor-cpsat-1',
        circuit_hash=fingerprint(circuit),fault_inventory_hash=sha256(json.dumps([f.to_dict() for f in faults],sort_keys=True).encode()).hexdigest(),
        forward_effect_hash=sha256(json.dumps(effects).encode()).hexdigest(),
        physical_variants=len(faults),physical_locations=len(locations),
        parameters=dict(max_time_in_seconds=seconds,max_deterministic_time=deterministic_time,num_search_workers=1,random_seed=0),
        runtime_seconds=time.perf_counter()-started,forward_seconds=forward-started,model_seconds=built-forward,
        solver_wall_seconds=solver.wall_time,num_conflicts=solver.num_conflicts,num_branches=solver.num_branches,
        solver_response=solver.response_stats(),proof_payload='exported CP-SAT model plus input hashes; rerun required, no portable UNSAT proof')
    if status in (cp_model.FEASIBLE,cp_model.OPTIMAL):
        selected=[f.to_dict() for i,f in enumerate(faults) if solver.value(variables[i])]
        actual=replay(circuit.to_dict(),selected)
        result['violating_faults']=selected;result['physical_replay']=actual
        if actual['detector_outcomes'] or not actual['logical_coset']:raise ArithmeticError('SAT witness failed physical replay')
    return result
