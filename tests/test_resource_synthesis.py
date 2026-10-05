"""Scientific boundary tests: actual physical edits, signed sectors and audits."""
from dataclasses import replace
import json
from pathlib import Path
import pytest
from ftqec.codes.stabilizer import StabilizerCode
from ftqec.architectures.generators import generate
from ftqec.circuits.memory import MemoryConfig, build_memory
from ftqec.resource_synthesis.design import Design, basis_mutations, basis_code, multiply
from ftqec.resource_synthesis.circuits import build_design, validate_ideal
from ftqec.resource_synthesis.certification import evaluate, classify, SignatureCache, independent_audit
from ftqec.resource_synthesis.operators import compressions
from ftqec.resource_synthesis.pareto import Archives, tiers
from ftqec.resource_synthesis.search import ResourceConfig, run_resource_search, retain_valid, OperatorStatistics, protection_audit
from ftqec.faults.signatures import signatures
from ftqec.evaluation.resources import resources

ROOT=Path(__file__).resolve().parents[1]

@pytest.fixture
def code(): return StabilizerCode.from_dict(json.loads((ROOT/'benchmarks/development_v2/pool/steane7.json').read_text()))

def row(name,q,d,g,lo,hi=None):
    return {'architecture_id':name,'resources':{'Q':q,'D':d,'QD':q*d,'two_q_gates':g},
            'bounds':{'lower_bound':lo,'upper_bound':hi},'region':classify({'lower_bound':lo,'upper_bound':hi},3)}

def test_regions_unknown_and_distance_conditioned_tradeoffs():
    a=row('a',10,30,60,3); b=row('b',12,20,70,4); c=row('c',9,10,10,2,2)
    assert c['region']=='INVALID'
    assert classify({'lower_bound':2,'upper_bound':None},3)=='UNKNOWN'
    ts=tiers([a,b,c]); assert set(ts['3']['architecture_ids'])=={'a','b'}
    assert ts['4']['architecture_ids']==['b']; assert ts['3']['minima']['Q']==10
    archive=Archives(3); [archive.update(r) for r in (a,b,c)]
    assert {r['architecture_id'] for r in archive.valid}=={'a','b'}
    assert [r['architecture_id'] for r in archive.near]==['c']
    assert retain_valid(a,c,3) is a

def test_original_memory_resources_and_physical_signatures_match(code):
    a=next(iter(generate(code,1,10))); memory=MemoryConfig(basis='X')
    c=build_design(code,Design(a),memory); old=build_memory(code,a,memory)
    assert validate_ideal(c)['verified']; assert resources(c)==resources(old)
    # Detector ordering differs; physical validity/exclusion are unchanged.
    from ftqec.faults.search import search_faults
    assert search_faults(c,signatures(c),2)['lower_bound']==search_faults(old,signatures(old),2)['lower_bound']

def test_real_flag_removal_reuse_and_schedule(code):
    a=next(iter(generate(code,1,10)))
    a=replace(a,flag_intervals=tuple(((0,len(o)),(0,len(o))) for o in a.orders),
              syndrome_budget=len(a.orders),ancilla_assignment=tuple(range(len(a.orders))),parallelism=1)
    design=Design(a); c=build_design(code,design,MemoryConfig(basis='X'))
    options=compressions(design,c)
    assert {'remove_flag_ancilla','remove_one_flag_interaction','merge_flag_records','merge_flag_intervals',
            'reuse_syndrome_ancilla','reuse_flag_ancilla','remove_redundant_syndrome_measurement',
            'reduce_reset_measurement_cycles','increase_safe_parallelism'} <= {op for _,op,_ in options}
    for operator in ('remove_flag_ancilla','reuse_flag_ancilla','reuse_syndrome_ancilla','remove_redundant_syndrome_measurement'):
        child=next(d for d,op,_ in options if op==operator); cc=build_design(code,child,MemoryConfig(basis='X'))
        assert validate_ideal(cc)['verified']
        assert resources(cc)['QD']!=resources(c)['QD'] or resources(cc)['two_q_gates']<resources(c)['two_q_gates']
    parallel=next(d for d,op,_ in options if op=='increase_safe_parallelism')
    assert resources(build_design(code,parallel,MemoryConfig(basis='X')))['D']<resources(c)['D']
    broken=next(d for d,op,_ in options if op=='remove_one_flag_interaction')
    assert not validate_ideal(build_design(code,broken,MemoryConfig(basis='X')))['verified']

def test_signed_basis_preservation_and_negative_row_rejection(code):
    a=next(iter(generate(code,1,10))); d=Design(a)
    for child,_ in basis_mutations(code,d,8):
        changed=basis_code(code,child)
        assert changed.rank==code.rank; assert all(code.is_stabilizer(g) for g in changed.generators)
        assert validate_ideal(build_design(code,child,MemoryConfig(basis='X')))['verified']
        assert build_design(code,child,MemoryConfig(basis='X')).experiment['logical_pauli']==build_design(code,d,MemoryConfig(basis='X')).experiment['logical_pauli']
    negative=StabilizerCode.from_dict({'generators':['XX','ZZ']})
    assert multiply(*negative.generators)[1]==2
    nd=Design(next(iter(generate(negative,1,0))))
    assert basis_mutations(negative,nd)==[]
    bad=replace(nd,candidate=replace(nd.candidate,generating_basis=('YY','ZZ')))
    with pytest.raises(ValueError,match='Signed'): basis_code(negative,bad)

def test_delta_suffix_reuse_agrees_with_independent_forward(code):
    a=next(iter(generate(code,1,10))); d=Design(a); memory=MemoryConfig(basis='X')
    c=build_design(code,d,memory); cache=SignatureCache(); cache.get(c)
    from ftqec.resource_synthesis.certification import fingerprint
    child=replace(d,candidate=replace(a,orders=(tuple(reversed(a.orders[0])),)+a.orders[1:]))
    cc=build_design(code,child,memory); ss,delta=cache.get(cc,fingerprint(c))
    assert delta['reused_suffix_operations']>0
    assert ss==signatures(cc)==signatures(cc,backend='forward')
    changed=replace(d,omitted_checks=((0,0),))
    dc=build_design(code,changed,memory); ds,stats=cache.get(dc,fingerprint(c))
    assert ds==signatures(dc); assert stats['reused_suffix_operations']==0

def test_cat_family_ideal_and_independent_exclusion(code):
    d=Design(next(iter(generate(code,1,10))),family='verified_cat')
    rec,c=evaluate(code,d,MemoryConfig(basis='X'),3)
    assert validate_ideal(c)['verified']; assert any(op.role=='cat_entangle' for op in c.operations)
    assert any(op.role=='cat_verify_close' for op in c.operations)
    assert independent_audit(rec,c,3)['verified']

def test_operator_stats_mean_and_rollback():
    parent=row('p',12,20,100,3); child=row('c',10,10,80,3); broken=row('b',8,8,50,2,2)
    stats=OperatorStatistics(); stats.observe('remove',parent,child,True); stats.observe('remove',parent,broken,False)
    s=stats.to_dict()['remove']; assert s['valid_survivors']==1; assert s['dc_failures']==1
    assert s['mean_saved']['Q']==3; assert s['probability_eliminates_source_class_representative']==.5
    assert retain_valid(parent,broken,3) is parent; assert retain_valid(parent,child,3) is child

def test_search_slots_final_certification_and_local_audit(code):
    result=run_resource_search(code,MemoryConfig(basis='X'),ResourceConfig(budget=8,initial_population=2))
    assert len(result['records'])==8
    assert all(a['verified'] for a in result['independent_final_audits'])
    assert set(result['archives']) >= {'VALID_PARETO','NEAR_VALID_PARETO'}
    # A tiny repetition-memory fixture makes exhaustive removal audit inexpensive.
    simple=StabilizerCode.from_dict({'generators':['ZZI','IZZ']})
    d=Design(next(iter(generate(simple,1,0))))
    cfg=ResourceConfig(target_dc=2,budget=2)
    rec,_=evaluate(simple,d,MemoryConfig(basis='Z'),2)
    assert rec['region']=='VALID'
    audit=protection_audit(simple,d,MemoryConfig(basis='Z'),cfg)
    assert audit['global_optimality_claim'] is False
    assert all(r['classification'] in ('REMOVABLE','UNKNOWN','EMPIRICALLY_NECESSARY','PROVABLY_NECESSARY_WITHIN_TESTED_MODEL') for r in audit['removals'])
