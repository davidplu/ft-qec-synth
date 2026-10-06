from dataclasses import replace
from itertools import combinations
from ftqec.codes.stabilizer import StabilizerCode
from ftqec.architectures.generators import generate
from ftqec.circuits.memory import MemoryConfig
from ftqec.resource_synthesis.design import Design
from ftqec.resource_synthesis.circuits import build_design
from ftqec.resource_synthesis.certification import SignatureCache
from ftqec.faults.search import search_faults
from ftqec.certification_v5.exact import certify,canonical_types,realization
from ftqec.certification_v5.independent import exclusion
from ftqec.certification_v5.staged import Budget,unknown_frontier,priority,escalate
from ftqec.certification_v5.descent import descend


def small():
    code=StabilizerCode.from_dict(dict(n=3,generators=['ZZI','IZZ']))
    d=Design(next(iter(generate(code,1,10))))
    c=build_design(code,d,MemoryConfig(rounds=1,basis='Z'))
    ss,_=SignatureCache().get(c)
    return code,d,c,ss


def test_mitm_equals_physical_naive_and_separate_trellis():
    _,_,c,ss=small()
    b=certify(c,ss,4); old=search_faults(c,ss,3,1000000)
    assert (b['lower_bound'],b['upper_bound'])==(old['lower_bound'],old['upper_bound'])
    assert exclusion(c,b['lower_bound']-1)['verified']
    assert b['certificate']['circuit_hash']


def test_location_matching_retains_alternatives_and_rejects_hall_failure():
    _,_,_,ss=small(); s=ss[0]
    def entry(loc): return replace(s,fault=replace(s.fault,location=loc))
    types=[((1,0),{'a':entry('a'),'b':entry('b')}),((2,0),{'a':entry('a')})]
    r=realization(types,(0,1)); assert len({x.fault.location for x in r})==2
    types[0][1].pop('b'); assert realization(types,(0,1)) is None


def test_caps_do_not_certify_incomplete_weight():
    _,_,c,ss=small()
    b=certify(c,ss,7,0); assert b['lower_bound']==1 and b['status']=='UNKNOWN'
    b=certify(c,ss,7,1000000,1); assert b['reason']=='table_limit'
    assert not exclusion(c,2,state_limit=1)['verified']


def test_duplicate_and_zero_types_preserve_small_exact_distance():
    _,_,c,ss=small(); b=certify(c,ss,4)
    duplicate=ss+ss; other=certify(c,duplicate,4)
    assert b['lower_bound']==other['lower_bound'] and b['upper_bound']==other['upper_bound']
    assert len(canonical_types(ss))==len(canonical_types(duplicate))


def row(name,q,d,region):
    return dict(architecture_id=name,resources=dict(Q=q,D=d,QD=q*d,two_q_gates=d),
                region=region,bounds=dict(lower_bound=2,upper_bound=None))


def test_unknown_archive_preserves_tradeoffs_without_false_validity():
    rows=[row('v',5,5,'VALID'),row('u',4,8,'UNKNOWN'),row('dominated',6,6,'UNKNOWN')]
    assert [r['architecture_id'] for r in unknown_frontier(rows)]==['u']
    assert priority(rows[1],rows,3)==priority(rows[1],rows,3)
    assert rows[1]['region']=='UNKNOWN'


def test_escalation_separate_budget_and_independent_promotion():
    _,d,c,_=small(); r=row(d.id,4,10,'UNKNOWN'); r['bounds']['lower_bound']=1
    budget=Budget(limit=1000000); out=escalate(r,c,3,budget)
    assert out['region']=='VALID' and out['independent_audit']['verified']
    assert budget.used>0 and budget.candidate_evaluations==1 and budget.events
    empty=Budget(limit=0); assert escalate(r,c,3,empty)['region']=='UNKNOWN'


def test_descent_budget_cannot_claim_minimality():
    from ftqec.evaluation.resources import resources
    code,d,_,_=small(); memory=MemoryConfig(rounds=3,basis='Z')
    c=build_design(code,d,memory); ss,_=SignatureCache().get(c); b=certify(c,ss,3)
    parent=dict(architecture_id=d.id,design=d.to_dict(),resources=resources(c),bounds=b,
                region='VALID',circuit_hash=b['certificate']['circuit_hash'])
    result=descend(code,memory,[parent],3,Budget(0),evaluation_limit=0)
    assert result['new_evaluations']==0
    assert all(x['label']!='LOCALLY_PROTECTION_MINIMAL_1' for x in result['audits'].values())


def test_serialized_certificate_detects_inventory_or_circuit_tampering():
    import json
    from ftqec.certification_v5.artifacts import verify
    _,_,c,ss=small(); b=json.loads(json.dumps(certify(c,ss,3)))
    assert verify(c,b)['verified']
    b['certificate']['fault_inventory_hash']='tampered'
    assert verify(c,b)['field']=='fault_inventory_hash'


def test_completed_descent_has_no_certified_reducing_single_edit():
    from ftqec.evaluation.resources import resources
    code,d,_,_=small(); memory=MemoryConfig(rounds=3,basis='Z')
    c=build_design(code,d,memory);ss,_=SignatureCache().get(c);b=certify(c,ss,3)
    parent=dict(architecture_id=d.id,design=d.to_dict(),resources=resources(c),bounds=b,
                region='VALID',circuit_hash=b['certificate']['circuit_hash'])
    result=descend(code,memory,[parent],3,Budget(1000000),evaluation_limit=500)
    assert not result['stopped_by_budget']
    for key in result['frontier']:
        audit=result['audits'][key]
        assert audit['label']=='LOCALLY_PROTECTION_MINIMAL_1'
        assert not any(r['region']=='VALID' for r in audit['edits'])
    assert result['minima']['QD']<parent['resources']['QD']


def test_cleanup_removes_only_disconnected_unobserved_components():
    from ftqec.certification_v5.cleanup import disconnected_ancillas
    from ftqec.circuits.model import Circuit
    _,_,c,_=small();extra=c.num_qubits
    c.flag_qubits=c.flag_qubits+(extra,)
    c.add('RESET',[extra]);c.add('M',[extra],record='orphan')
    c.validate();clean,proof=disconnected_ancillas(c)
    assert proof['removed_qubits']==[extra] and proof['removed_operations']==2
    assert clean.num_qubits==extra
    c.detectors.append(['orphan']);c.detector_offsets.append(0)
    kept,proof=disconnected_ancillas(c)
    assert not proof['removed_qubits'] and kept.num_qubits==extra+1


def test_depth_two_requires_exhausted_or_bounded_single_descent():
    import pytest
    from ftqec.certification_v5.rescue import depth_two
    code,d,c,ss=small()
    parent=dict(architecture_id=d.id,design=d.to_dict(),resources=dict(Q=4,D=10,QD=40,two_q_gates=4))
    with pytest.raises(ValueError):
        depth_two(code,MemoryConfig(rounds=1),parent,dict(label='NOT_LOCALLY_PROTECTION_MINIMAL'),3,Budget(0))


def test_higher_target_channel_exclusion_is_not_full_quantum_distance_claim():
    code=StabilizerCode.from_dict(dict(n=5,generators=['ZZIII','IZZII','IIZZI','IIIZZ']))
    d=Design(next(iter(generate(code,1,10))));c=build_design(code,d,MemoryConfig(rounds=1,basis='Z'))
    ss,_=SignatureCache().get(c);b=certify(c,ss,6,1000000)
    assert b['lower_bound']==5 and b['upper_bound']==5 and b['status']=='EXACT'
    assert exclusion(c,4,state_limit=250000,work_limit=2000000)['verified']
    assert code.k==1  # Z on one data qubit is logical: quantum distance remains 1.


def test_independent_logical_group_audit_matches_full_physical_pairs():
    from ftqec.certification_v5.low_audit import exclude
    from ftqec.faults.exclusion import verify_exclusion
    code=StabilizerCode.from_dict(dict(n=3,generators=['ZZI','IZZ']))
    for candidate in generate(code,6,11):
        for axis in ('X','Z'):
            c=build_design(code,Design(candidate),MemoryConfig(rounds=2,basis=axis))
            assert exclude(c,2)['verified']==verify_exclusion(c,2)['verified']


def test_pair_representative_kernel_preserves_every_two_location_forbidden_set():
    import random
    from ftqec.certification_v5.pair_audit import kernel
    rng=random.Random(10)
    for _ in range(50):
        edges=[(a,b,a,b) for a,b in combinations(range(8),2) if rng.random()<0.5]
        family=[]
        for edge in edges:family,_=kernel(family+[edge])
        assert len(family)<=12
        for size in (0,1,2):
            for forbidden in combinations(range(8),size):
                assert any(set(e[:2]).isdisjoint(forbidden) for e in edges)==any(set(e[:2]).isdisjoint(forbidden) for e in family)


def test_independent_pair_audit_matches_small_exact_and_replays_witness():
    from ftqec.certification_v5.pair_audit import exclusion as pair_exclusion
    _,_,c,ss=small();exact=certify(c,ss,5)
    checked=pair_exclusion(c,4)
    assert not checked['verified'] and checked['witness']['fault_count']==exact['upper_bound']
    assert pair_exclusion(c,2)['verified']
    capped=pair_exclusion(c,4,work_limit=0)
    assert not capped['verified'] and capped['excluded_through']==2


def test_sat_full_physical_model_matches_small_exact_and_replays_violation():
    # Explicit verification dependency: absence is an error, not a silent skip.
    from ftqec.certification_v5.sat_audit import exclusion as sat_exclusion
    _,_,c,_=small()
    assert sat_exclusion(c,2,seconds=5)['verified']
    out=sat_exclusion(c,3,seconds=5)
    assert out['status'] in ('OPTIMAL','FEASIBLE') and len(out['violating_faults'])==3


def test_projection_has_physical_relations_without_adding_scientific_detectors():
    import copy
    from ftqec.certification_v5.projection import certify as projection_certify,verify as projection_verify
    code=StabilizerCode.from_dict(dict(n=9,generators=['ZZIIIIIII','IZZIIIIII','IIIZZIIII','IIIIZZIII',
        'IIIIIIZZI','IIIIIIIZZ','XXXXXXIII','IIIXXXXXX']))
    d=Design(next(iter(generate(code,1,10))));c=build_design(code,d,MemoryConfig(rounds=1,basis='X'))
    before=c.to_dict();cert=projection_certify(c)
    assert cert['lower_bound']==3 and cert['coordinate_count']==3
    assert c.to_dict()==before
    assert projection_verify(c,cert)['verified']
    changed=copy.deepcopy(cert);changed['lower_bound']=4
    assert not projection_verify(c,changed)['verified']
    changed=copy.deepcopy(cert);changed['detector_combinations'][1]^=1
    assert not projection_verify(c,changed)['verified']
    ss,_=SignatureCache().get(c);b=certify(c,ss,4)
    assert b['upper_bound']==cert['lower_bound']


def test_public_cli_search_keeps_separate_completion_budget(tmp_path):
    import json
    from ftqec.certification_v5.entrypoint import main
    code,_,_,_=small();p=tmp_path/'code.json';out=tmp_path/'result.json'
    p.write_text(json.dumps(code.to_dict()))
    main(['search',str(p),'-o',str(out),'--budget','1','--descent-evaluations','0','--final-audit-evaluations','0'])
    result=json.loads(out.read_text())
    assert result['schema_version']=='0.5' and result['evaluation_slots']==1
    assert result['compression_descent']['new_evaluations']==0
    assert result['final_audit_completion']['descent']['new_evaluations']==0
    assert result['archives']['UNKNOWN_PARETO']==[]


def test_public_cli_projection_certificate_serializes_and_matches_schema(tmp_path):
    import json,jsonschema
    from pathlib import Path
    from ftqec.certification_v5.entrypoint import main
    code,d,_,_=small();p=tmp_path/'code.json';design=tmp_path/'design.json';out=tmp_path/'cert.json'
    p.write_text(json.dumps(code.to_dict()));design.write_text(json.dumps(d.to_dict()))
    main(['certify',str(p),'--design',str(design),'-o',str(out),'--target-dc','3','--rounds','1'])
    result=json.loads(out.read_text());assert result['bounds']['status']=='EXACT'
    assert result['independent_verification']['verified']
    schema=json.loads((Path(__file__).resolve().parents[1]/'benchmarks/certification_v5/certificate.schema.json').read_text())
    jsonschema.validate(result['bounds'],schema)


def test_canonical_set_order_normalization_preserves_physical_circuit():
    from dataclasses import replace
    from ftqec.certification_v5.canonical import normalize
    from ftqec.resource_synthesis.certification import fingerprint
    code,d,_,_=small();memory=MemoryConfig(rounds=3,basis='Z')
    a=replace(d,omitted_checks=((2,0),(1,0),(2,0)),omitted_terminal=(1,0,1))
    b=normalize(a)
    assert b.omitted_checks==((1,0),(2,0)) and b.omitted_terminal==(0,1)
    assert normalize(b)==b
    assert b.candidate==a.candidate and b.merged_records==a.merged_records
    assert fingerprint(build_design(code,a,memory))==fingerprint(build_design(code,b,memory))


def test_canonical_completion_rejects_changed_physical_certificate():
    import pytest
    from ftqec.certification_v5.canonical import complete
    code,d,c,ss=small();b=certify(c,ss,3)
    row=dict(architecture_id=d.id,design=d.to_dict(),circuit_hash='tampered',bounds=b,region='VALID')
    with pytest.raises(ArithmeticError,match='physical circuit'):
        complete(code,MemoryConfig(rounds=1),[row],[d.id],3,evaluation_limit=0)


def test_serialized_evidence_rejects_witness_weight_overstatement():
    import copy
    from ftqec.certification_v5.evidence import verify
    _,_,c,ss=small();b=certify(c,ss,4)
    assert verify(c,b)['verified']
    bad=copy.deepcopy(b);bad['witness']['fault_count']+=1
    assert not verify(c,bad)['verified']
    bad=copy.deepcopy(b);bad['upper_bound']+=1
    assert not verify(c,bad)['verified']
