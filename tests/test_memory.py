import json, random
from pathlib import Path
import pytest
import jsonschema
from ftqec.codes.stabilizer import StabilizerCode
from ftqec.architectures.generators import generate
from ftqec.circuits.memory import MemoryConfig,build_memory
from ftqec.circuits.model import Circuit
from ftqec.faults.signatures import signatures,Fault,Signature
from ftqec.faults.search import search_faults
from ftqec.faults.verification import replay,verify_witness
from ftqec.decoding.minimum_weight import BoundedMinimumWeightDecoder,decoder_failures
from ftqec.faults.analysis import analyze,transport_witness
from ftqec.search.repairs import targeted_repairs
from ftqec.search.cegis import run_search,SearchConfig
from dense_memory_oracle import dense_run

ROOT=Path(__file__).resolve().parents[1]
def simple(basis='Z',noisy_input=False):
    code=StabilizerCode.from_dict({'generators':['ZZ']})
    return build_memory(code,next(generate(code,1)),MemoryConfig(3,basis,noisy_input=noisy_input))

def test_no_fault_and_roundtrip():
    c=simple(); out=replay(c.to_dict(),[])
    assert out['detector_outcomes']==out['logical_coset']==out['flag_outcomes']==0
    assert Circuit.from_dict(c.to_dict()).to_dict()==c.to_dict()
    schema=json.loads((ROOT/'docs/schemas/circuit.schema.json').read_text())
    jsonschema.validate(c.to_dict(),schema)

@pytest.mark.parametrize('round_index,pattern',[(0,3),(1,6),(2,12)])
def test_measurement_temporal_pattern(round_index,pattern):
    c=simple(); s=next(s for s in signatures(c) if s.fault.role=='syndrome_readout' and s.fault.round_index==round_index)
    assert s.detectors==pattern; assert s.logical==0
    assert replay(c,[s.fault])['detector_outcomes']==pattern

def test_persistent_data_fault():
    c=simple(); s=next(s for s in signatures(c) if s.fault.role=='data_interaction' and s.fault.round_index==0 and s.fault.qubits[-1]==0 and s.fault.label=='IX')
    assert s.detectors==2
    out=replay(c,[s.fault]); assert out['measurement_record_effects']['s0:r1']==out['measurement_record_effects']['s0:r2']==1

def test_reset_fault_and_boundaries():
    c=simple(noisy_input=True)
    reset=next(s for s in signatures(c) if s.fault.role=='syndrome_reset' and s.fault.round_index==1 and s.fault.label=='X')
    assert reset.detectors==6 and reset.logical==0
    prep=next(s for s in signatures(c) if s.fault.kind=='preparation' and s.fault.qubits==(0,) and s.fault.label=='X')
    assert prep.detectors==1 and prep.logical==1
    final=next(s for s in signatures(c) if s.fault.role=='final_data_readout' and s.fault.qubits==(0,))
    assert final.detectors==8 and final.logical==1

@pytest.mark.parametrize('name',['css4','noncss4','perfect5','steane'])
@pytest.mark.parametrize('basis',['X','Z'])
def test_suffix_vs_forward_every_signature(name,basis):
    code=StabilizerCode.from_dict(json.loads((ROOT/f'benchmarks/development/{name}.json').read_text()))
    for candidate in generate(code,3,7):
        c=build_memory(code,candidate,MemoryConfig(2,basis, noisy_input=True))
        assert signatures(c,True)==signatures(c,True,backend='forward')

@pytest.mark.parametrize('name',['css4','noncss4'])
@pytest.mark.parametrize('basis',['X','Z'])
def test_dense_actual_states_confirm_temporal_and_logical_semantics(name,basis):
    code=StabilizerCode.from_dict(json.loads((ROOT/f'benchmarks/development/{name}.json').read_text()))
    c=build_memory(code,next(generate(code,1)),MemoryConfig(2,basis))
    ss=signatures(c)
    rng=random.Random(11)
    for seed in range(4):
        assert dense_run(c,seed=seed)==(0,0,0)
        group=rng.sample(ss,2)
        if group[0].fault.location==group[1].fault.location: continue
        expected=replay(c,[s.fault for s in group])
        assert dense_run(c,[s.fault for s in group],seed)==(expected['detector_outcomes'],expected['logical_coset'],expected['flag_outcomes'])

@pytest.mark.parametrize('basis',['X','Z'])
def test_witness_verified_against_dense_replay(basis):
    code=StabilizerCode.from_dict({'generators':['XXXX','ZZZZ']})
    c=build_memory(code,next(generate(code,1)),MemoryConfig(3,basis))
    out=search_faults(c,signatures(c),3)
    assert out['status']=='EXACT'; assert out['upper_bound'] in (1,2)
    w=out['witness']; assert verify_witness(c.to_dict(),w)['verified']
    assert dense_run(c,[Fault.from_dict(f) for f in w['faults']],0)==(0,w['logical_coset'],0)
    broken={**w,'logical_coset':w['logical_coset']^1}
    assert not verify_witness(c,broken)['verified']
    with pytest.raises(ValueError): replay(c,[w['faults'][0],w['faults'][0]])

def test_decoder_failure_distinct_from_circuit_distance():
    ss=[Signature(Fault(0,(0,),'X','idle','a'),1,0,0,0),Signature(Fault(1,(0,),'Z','idle','b'),1,0,1,0)]
    decoder=BoundedMinimumWeightDecoder().fit(ss)
    failures=decoder_failures(ss,decoder)
    assert failures['failures']==1
    assert failures['witnesses'][0]['detector_signature']==1
    assert decoder.predict_logical(2) is None
    c=simple(); assert search_faults(c,ss,1)['lower_bound']==2

def test_higher_weight_fallback_and_work_limit():
    c=simple()
    ss=[Signature(Fault(i,(0,),'X','idle',str(i)),d,0,l,0) for i,(d,l) in enumerate([(1,0),(2,0),(4,0),(7,1)])]
    assert search_faults(c,ss,4)['upper_bound']==4
    assert search_faults(c,ss,4,0)['status']=='UNRESOLVED'

def test_counterexample_analysis_and_repair_provenance():
    code=StabilizerCode.from_dict({'generators':['XXXX','ZZZZ']}); parent=next(generate(code,1))
    c=build_memory(code,parent,MemoryConfig(2,'Z')); ss=signatures(c); w=search_faults(c,ss,3)['witness']
    a=analyze(c,w,ss)
    assert a.total_fault_weight==w['fault_count']; assert a.rounds
    for child,p in targeted_repairs(parent,a,random.Random(0)):
        child.validate(code)
        assert p.kind=='COUNTEREXAMPLE_GUIDED' and p.source_counterexample_id==a.counterexample_id
        assert p.failure_class and p.repair_operator
        mapped,reason=transport_witness(c,build_memory(code,child,MemoryConfig(2,'Z')),w)
        assert mapped is not None or reason

@pytest.mark.parametrize('strategy',['random','resource','cegis','mixed'])
def test_budget_matched_deterministic_search(strategy):
    code=StabilizerCode.from_dict({'generators':['XXXX','ZZZZ']})
    cfg=SearchConfig(budget=10,strategy=strategy,max_combinations=10000)
    a=run_search(code,MemoryConfig(2),cfg); b=run_search(code,MemoryConfig(2),cfg)
    def decisions(d):
        return [(r['architecture_id'],r['bounds'],r['provenance'],r.get('repair_outcome')) for r in d['records']]
    assert decisions(a)==decisions(b); assert a['evaluation_slots']==10; assert a['mutation_count']==4
    if strategy=='cegis': assert any(r['provenance']['kind']=='COUNTEREXAMPLE_GUIDED' for r in a['records'])

def test_identical_initial_population_across_ablations():
    code=StabilizerCode.from_dict({'generators':['XXXX','ZZZZ']})
    ids=[run_search(code,MemoryConfig(2),SearchConfig(budget=6,strategy=s))['initial_population_ids'] for s in ['random','resource','cegis','mixed']]
    assert all(i==ids[0] for i in ids)


def test_v02_result_native_schema():
    code=StabilizerCode.from_dict({'generators':['XXXX','ZZZZ']})
    result=run_search(code,MemoryConfig(2),SearchConfig(budget=10))
    schema=json.loads((ROOT/'docs/schemas/result-v0.2.schema.json').read_text())
    jsonschema.validate(result,schema)

def test_idle_fault_verifier_and_forged_location():
    c=simple(); s=next(s for s in signatures(c,True) if s.fault.kind=='idle')
    assert replay(c,[s.fault])['detector_outcomes']==s.detectors
    fault=s.fault.to_dict(); fault['location']='idle:0:999999'
    with pytest.raises(ValueError): replay(c,[fault])
    fault=next(s.fault.to_dict() for s in signatures(c) if s.fault.kind=='measurement')
    fault['location']='forged'
    with pytest.raises(ValueError): replay(c,[fault])

def test_flagged_dense_noiseless_epochs():
    code=StabilizerCode.from_dict({'generators':['XXXX','ZZZZ']})
    from dataclasses import replace
    candidate=replace(next(generate(code,1)),flag_intervals=(((0,4),),()))
    circuit=build_memory(code,candidate,MemoryConfig(2))
    assert dense_run(circuit,seed=4)==(0,0,0)
    ss=signatures(circuit)
    fault=next(s for s in ss if s.fault.role=='flag_readout')
    assert dense_run(circuit,[fault.fault],4)==(fault.detectors,fault.logical,fault.flags)


def test_all_logical_indices_and_input_validation():
    code=StabilizerCode.from_dict({'generators':['XXXX','ZZZZ']})
    candidate=next(generate(code,1))
    for index in range(code.k):
        for basis in ['X','Z']:
            c=build_memory(code,candidate,MemoryConfig(2,basis,index))
            assert dense_run(c,seed=5)==(0,0,0)
    with pytest.raises(ValueError): build_memory(code,candidate,MemoryConfig(2,'Z',code.k))
    with pytest.raises(ValueError): MemoryConfig(0)
    with pytest.raises(ValueError): SearchConfig(budget=0)

def test_repair_source_elimination_and_quality_gain_are_distinct():
    from dataclasses import replace
    from ftqec.search.cegis import evaluate_memory,repair_outcome
    code=StabilizerCode.from_dict({'generators':['XXXX','ZZZZ']})
    parent=next(generate(code,1)); child=replace(parent,flag_intervals=(((0,4),),()))
    config=SearchConfig(budget=2,max_combinations=100000)
    p,pc=evaluate_memory(code,parent,MemoryConfig(3,'Z'),config)
    c,cc=evaluate_memory(code,child,MemoryConfig(3,'Z'),config)
    outcome=repair_outcome(p,c,pc,cc)
    assert outcome['eliminates_source_witness']
    assert outcome['improves_distance_lower_bound']
    assert c['bounds']['upper_bound']==2
    assert c['bounds']['lower_bound']==2
    assert not c['bounds']['lower_bound']>=config.target_dc

def test_repeated_cli_memory_faults_decode_verify(tmp_path):
    from ftqec.cli import main
    code=ROOT/'benchmarks/development/css4.json'
    circuit=tmp_path/'c.json'; fault=tmp_path/'f.json'; verification=tmp_path/'v.json'
    main(['memory',str(code),'--rounds','2','--basis','X','-o',str(circuit)])
    main(['faults',str(circuit),'--max-weight','3','-o',str(fault)])
    main(['verify',str(circuit),'--witness',str(fault),'-o',str(verification)])
    assert json.loads(verification.read_text())['verified']
    main(['decode',str(circuit),'-o',str(tmp_path/'d.json')])
    assert json.loads((tmp_path/'d.json').read_text())['training_completed_through']==1


def test_explicit_idle_is_a_gate_location_not_a_virtual_tick():
    c=Circuit(StabilizerCode(1,()),(),()); c.add('IDLE',[0])
    ss=signatures(c)
    assert all(s.fault.kind=='idle_gate' for s in ss)
    w=search_faults(c,ss,1)['witness']
    assert verify_witness(c.to_dict(),w)['verified']

def test_dense_encoded_input_output_noise():
    c=simple(noisy_input=True)
    fault=next(s for s in signatures(c) if s.fault.kind=='preparation' and s.fault.qubits==(0,) and s.fault.label=='X')
    assert dense_run(c,[fault.fault],3)==(fault.detectors,fault.logical,fault.flags)
