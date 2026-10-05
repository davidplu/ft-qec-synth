from ftqec.resource_synthesis.audits import strict_minimality,class_eliminated
from ftqec.resource_synthesis.audits import constraint_evaluation
from ftqec.resource_synthesis.search import ResourceConfig
import json
from ftqec.resource_synthesis.entrypoint import main
from ftqec.resource_synthesis.design import Design
from ftqec.resource_synthesis.certification import evaluate
from ftqec.resource_synthesis.circuits import build_design
from ftqec.resource_synthesis.circuits import validate_ideal
from ftqec.faults.signatures import signatures
from ftqec.resource_synthesis.operators import compressions
from ftqec.codes.stabilizer import StabilizerCode
from ftqec.architectures.generators import generate
from ftqec.circuits.memory import MemoryConfig

def test_minimality_rejects_cheaper_valid_tradeoff_and_unknown():
    parent={'Q':10,'D':10,'QD':100,'two_q_gates':20}
    tradeoff={'Q':9,'D':12,'QD':108,'two_q_gates':20}
    removal={'classification':'REMOVABLE','child':{'resources':tradeoff}}
    audit={'label':'LOCALLY_PROTECTION_MINIMAL','removals':[removal]}
    assert strict_minimality(audit,parent)['label']=='NOT_LOCALLY_PROTECTION_MINIMAL'
    removal['classification']='UNKNOWN'
    assert strict_minimality(audit,parent)['label']=='UNKNOWN'

def test_full_class_elimination_requires_all_mapped_realizations():
    members=[(0,1),(2,3)]
    effects={0:('a',1,1),1:('b',0,0),2:('c',1,1),3:('d',0,0)}
    assert class_eliminated(members,effects) is True
    effects[3]=('d',1,0)
    assert class_eliminated(members,effects) is False
    effects.pop(3)
    assert class_eliminated(members,effects) is None
    effects[3]=('c',0,0)
    assert class_eliminated(members,effects) is None

def test_cli_scientific_frontier_and_strict_audit(tmp_path):
    code={'generators':['ZZI','IZZ']}; source=tmp_path/'code.json'; source.write_text(json.dumps(code))
    output=tmp_path/'result.json'
    main(['search',str(source),'-o',str(output),'--target-dc','2','--budget','2','--basis','Z','--minimality','--select','Q'])
    result=json.loads(output.read_text()); assert result['schema_version']=='0.4'
    assert result['design_inventory']['bases'][0]['metrics']['overlaps']
    assert result['summary']['target_reached']; assert result['local_minimality']
    assert all('minimality_definition' in a for a in result['local_minimality'])
    selected=tmp_path/'frontier.json'
    main(['frontier',str(output),'--target-dc','2','-o',str(selected)])
    assert json.loads(selected.read_text())['architecture_ids']

def test_capped_screen_is_unknown_and_terminal_detector_removal_has_no_gate_saving():
    code=StabilizerCode.from_dict({'generators':['ZZI','IZZ']}); d=Design(next(iter(generate(code,1,0))))
    memory=MemoryConfig(basis='Z'); r,c=evaluate(code,d,memory,2,0)
    assert r['region']=='UNKNOWN'
    opts=compressions(d,c)
    child=next(d for d,op,_ in opts if op=='remove_redundant_terminal_verification')
    cc=build_design(code,child,memory)
    assert len(cc.detectors)==len(c.detectors)-1
    assert cc.operations==c.operations

def test_cat_controlled_y_has_deterministic_signed_ideal_parities():
    code=StabilizerCode.from_dict({'generators':['XYZI','ZYXI']})
    design=Design(next(iter(generate(code,1,0))),family='verified_cat')
    c=build_design(code,design,MemoryConfig(basis='X'))
    assert validate_ideal(c)['verified']
    assert any(op.role=='data_basis_before' for op in c.operations)
    assert signatures(c)==signatures(c,backend='forward')

def test_constraint_only_audit_keeps_normal_certificate_and_witness():
    code=StabilizerCode.from_dict({'generators':['ZZI','IZZ']}); memory=MemoryConfig(basis='Z')
    design=Design(next(iter(generate(code,1,0)))); cfg=ResourceConfig(target_dc=2)
    for d in [design]+[d for d,_,_ in compressions(design,build_design(code,design,memory))[:3]]:
        full,_=evaluate(code,d,memory,cfg.target_dc,cfg.max_combinations)
        fast,_=constraint_evaluation(code,d,memory,cfg)
        assert fast['bounds']==full['bounds']; assert fast['region']==full['region']
