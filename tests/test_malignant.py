import json
import random
from dataclasses import replace
from itertools import combinations
from pathlib import Path
import pytest
import jsonschema
from ftqec.codes.stabilizer import StabilizerCode
from ftqec.architectures.generators import generate
from ftqec.circuits.memory import MemoryConfig, build_memory
from ftqec.faults.signatures import signatures, Signature
from ftqec.faults.spectrum import classify, malignant_spectrum, spectrum_delta, boundary_class
from ftqec.faults.exclusion import verify_exclusion
from ftqec.faults.batch_verification import verify_batch, singleton_effects
from ftqec.faults.search import witness
from ftqec.faults.verification import verify_witness
from ftqec.search.malignant import (MalignantConfig, run_malignant_search, quality_key,
    malignant_dominates, select_beam, diverse_classes, greedy_coverage,
    classify_repair, bounded_compound, whole_class_result)
from ftqec.search.repairs import Provenance
from dense_memory_oracle import dense_run

ROOT = Path(__file__).resolve().parents[1]

def circuit():
    code = StabilizerCode.from_dict({'generators':['XXXX','ZZZZ']})
    return build_memory(code, next(generate(code,1)), MemoryConfig(2,'Z'))

def record(n=10, cost=100, lower=2, node=1):
    layers = {str(i):{'complete':True,'class_count':0 if i<lower else n,
        'raw_count':0 if i<lower else n*2,'signature_count':0 if i<lower else 1} for i in range(1,4)}
    return {'architecture_id':str(node), 'evaluation_index':node,'bounds':{'lower_bound':lower},
        'malignant_spectrum':{'layers':layers,'classes':[]},'resources':{m:cost for m in ('Q','D','QD','two_q_gates')},
        'partial_progress':False,'neutral_depth':0}

def test_equivalence_permutation_and_observable_equivalent_labels():
    c=circuit(); s=signatures(c)[0]
    alternate=replace(s,fault=replace(s.fault,label='Y'))
    assert classify(c,[s]).id==classify(c,[alternate]).id
    different=replace(s,fault=replace(s.fault,round_index=1))
    assert classify(c,[s]).id!=classify(c,[different]).id
    t=signatures(c)[20]
    assert classify(c,[s,t]).id==classify(c,[t,s]).id
    assert classify(c,[s]).id!=classify(c,[replace(s,logical=s.logical^1)]).id

def test_mechanisms_do_not_merge_distinct_hooks_or_checks():
    c=circuit(); s=signatures(c)[0]
    assert classify(c,[s]).id!=classify(c,[replace(s,data=s.data^3)]).id
    assert classify(c,[s]).id!=classify(c,[replace(s,fault=replace(s.fault,check=1))]).id

def test_spectrum_matches_brute_distinct_location_pairs():
    c=circuit(); ss=signatures(c); spectrum,_=malignant_spectrum(c,ss,2,1000000)
    for weight in (1,2):
        expected=[]
        for group in combinations(ss,weight):
            if len({s.fault.location for s in group})!=weight:continue
            d=l=0
            for s in group:d^=s.detectors;l^=s.logical
            if not d and l:expected.append(group)
        layer=spectrum['layers'][str(weight)]
        assert layer['complete']
        assert layer['raw_count']==len(expected)
        assert layer['class_count']==len({classify(c,g).id for g in expected})
        if expected:break

def test_capped_count_is_unknown_not_zero():
    c=circuit(); spec,_=malignant_spectrum(c,signatures(c),3,0)
    assert spec['layers']['1']['class_count'] is None
    assert not spec['layers']['1']['complete']
    assert spec['layers']['2']['reason']=='not_searched_above_frontier'

def test_complete_triple_join_matches_brute_toy():
    c=circuit();base=signatures(c)
    ss=[replace(base[i],detectors=d,logical=l) for i,d,l in ((0,1,1),(20,2,0),(40,3,0))]
    assert len({s.fault.location for s in ss})==3
    spec,_=malignant_spectrum(c,ss,3,1000)
    assert spec['layers']['1']['raw_count']==0
    assert spec['layers']['2']['raw_count']==0
    assert spec['layers']['3']['raw_count']==spec['layers']['3']['class_count']==1

def test_fault_quality_lexicographic_and_resource_tradeoff():
    parent=record(10,100);child=record(7,200,node=2)
    assert quality_key(child)<quality_key(parent)
    assert not malignant_dominates(parent,child)
    assert not malignant_dominates(child,parent)
    assert quality_key(record(100,1000,3))<quality_key(child)

def test_unknown_layer_cannot_dominate_or_improve():
    a=record(0,50,node=2);b=record(1,100)
    a['malignant_spectrum']['layers']['2'].update(complete=False,class_count=None,raw_count=None,signature_count=None)
    assert not malignant_dominates(a,b)
    assert quality_key(b)<quality_key(a)

def test_partial_progress_protected_with_bounded_expiry():
    parent=record(10,100);child=record(7,200,node=2)
    child.update(partial_progress=True,neutral_depth=1)
    config=MalignantConfig(beam_width=1,protected_slots=1)
    beam,front,reasons=select_beam([parent,child],2,config)
    assert beam==[child]
    assert any(r['decision']=='PROTECTED_PARTIAL_PROGRESS' for r in reasons)
    beam,_,_=select_beam([parent,child],10,config)
    assert len(beam)<=1

def test_source_elimination_not_net_improvement():
    p=record(5);c=record(8,node=2)
    assert classify_repair(p,c,True)['category']=='REGRESSION'
    assert classify_repair(p,record(5,node=2),True)['category']=='SOURCE_ONLY'
    assert spectrum_delta(p['malignant_spectrum'],c['malignant_spectrum'])['2']==3

def test_partial_source_class_cannot_claim_whole_elimination():
    assert whole_class_result([True,True],0,False) is None
    assert whole_class_result([True,True],1,True) is None
    assert whole_class_result([True,True],0,True) is True
    assert whole_class_result([True,False],0,True) is False

def test_compound_depth_bound_and_no_unknown_progress():
    p=record(10);c=record(5,node=2);cfg=MalignantConfig(compound_depth=3)
    assert bounded_compound(p,c,cfg)==(True,1)
    p['neutral_depth']=2
    assert bounded_compound(p,c,cfg)==(False,3)
    c['malignant_spectrum']['layers']['2'].update(complete=False,class_count=None)
    assert not bounded_compound(p,c,cfg)[0]

def test_greedy_cover_and_deterministic_operator_memory():
    c=next(generate(circuit().code,1));prov=Provenance('COUNTEREXAMPLE_GUIDED',failure_class='HOOK',repair_operator='flag')
    opts=[{'candidate':c,'provenance':prov,'covers':['a'],'estimated_added_cost':1},
          {'candidate':replace(c,terminal_repetitions=1),'provenance':prov,'covers':['a','b'],'estimated_added_cost':1}]
    assert greedy_coverage(opts)[0]['covers']==['a','b']
    assert greedy_coverage(opts,enabled=False)[0]['covers']==['a']
    assert greedy_coverage(opts,{('HOOK','flag'):(2,3)})==greedy_coverage(opts,{('HOOK','flag'):(2,3)})

def test_diverse_classes_span_checks_and_rounds():
    classes=[{'id':str(i),'weight':2,'logical_effect':1,'hook_support':[i],
        'mechanisms':[(i,i)],'multiplicity':10-i} for i in range(3)]
    selected=diverse_classes(classes,2)
    assert len(selected)==2 and selected[0]['id']!=selected[1]['id']

def test_boundary_failure_and_unsupported_scope():
    assert boundary_class({'faults':[{'role':'final_data_readout'}]})==('BOUNDARY_READOUT_FAILURE','UNSUPPORTED_REPAIR_CLASS')
    assert boundary_class({'faults':[{'role':'data_interaction'}]})[0]=='EXTRACTION_FAILURE'
    assert boundary_class({'faults':[{'role':'data_interaction'},{'role':'final_data_readout'}]})[1]=='TERMINAL_VERIFICATION_CANDIDATE'

def test_real_terminal_round_faults_resources_and_dense_semantics():
    c=circuit();candidate=next(generate(c.code,1));extra=build_memory(c.code,replace(candidate,terminal_repetitions=1),MemoryConfig(2,'Z'))
    assert extra.experiment['rounds']==3
    assert len(extra.operations)>len(c.operations)
    assert any(s.fault.round_index==2 and s.fault.role=='syndrome_readout' for s in signatures(extra))
    assert signatures(extra)==signatures(extra,backend='forward')
    for seed in range(2):
        result=dense_run(extra,[],seed)
        assert result[0]==0
    assert Candidate_roundtrip(extra.code,candidate)

def Candidate_roundtrip(code,candidate):
    from ftqec.architectures.candidate import Candidate
    assert Candidate.from_dict(candidate.to_dict()).id==candidate.id
    extra=replace(candidate,terminal_repetitions=1)
    extra.validate(code)
    assert Candidate.from_dict(extra.to_dict())==extra
    return True

def test_independent_exhaustive_exclusion_uses_replay():
    c=circuit()
    assert verify_exclusion(c,0)['verified']
    assert not verify_exclusion(c,1)['verified']

@pytest.mark.parametrize('flagged',[False,True])
def test_bit_lane_replay_matches_scalar_minimum_witnesses_and_tamper(flagged):
    c=circuit()
    if flagged:c=build_memory(c.code,list(generate(c.code,2))[1],MemoryConfig(2,'Z'))
    ss=signatures(c);spec,_=malignant_spectrum(c,ss,2,100000)
    witnesses=[witness(c,[ss[i] for i in cls['representative_indices']]).to_dict() for cls in spec['classes']]
    assert witnesses
    assert all(verify_witness(c,w)['verified'] for w in witnesses)
    assert verify_batch(c,witnesses)['verified']
    bad=[{**witnesses[0],'logical_coset':0}]+witnesses[1:]
    assert not verify_batch(c,bad)['verified']
    with pytest.raises(ValueError):verify_batch(c,[{**witnesses[0],'fault_count':99}])

def test_bit_lane_replay_virtual_idles_and_legacy_logicals():
    from ftqec.circuits.extraction import build
    code=StabilizerCode.from_dict({'generators':['ZZ']});candidate=next(generate(code,1))
    for c in (build(code,candidate),build_memory(code,candidate,MemoryConfig(2,'X'))):
        ss=signatures(c,True)
        assert singleton_effects(c,[s.fault for s in ss])==[(s.detectors,s.logical) for s in ss]
        # A single data Z has an undetected X-memory/logical effect; measurement
        # and trailing-idle realizations exercise before/after boundary handling.
        found=[witness(c,[s]).to_dict() for s in ss if not s.detectors and s.logical]
        assert found and any(w['faults'][0]['kind']=='idle' for w in found)
        assert all(verify_witness(c,w)['verified'] for w in found)
        assert verify_batch(c,found)['verified']

def test_deterministic_search_ancestry_matched_budgets_and_schema():
    code=circuit().code;config=MalignantConfig(budget=9,initial_population=3,seed=2,max_weight=2,target_dc=2)
    a=run_malignant_search(code,MemoryConfig(2,'Z'),config)
    b=run_malignant_search(code,MemoryConfig(2,'Z'),config)
    assert [r['architecture_id'] for r in a['records']]==[r['architecture_id'] for r in b['records']]
    assert a['selection_history']==b['selection_history']
    assert a['evaluation_slots']==9 and a['mutation_count']==6
    for r in a['records']:
        assert r['parent_node'] is None or r['parent_node']<r['evaluation_index']
        if r.get('dc_delta',0)>0:assert r['independent_exclusion']['verified']
    for chain in a['distance_gain_chains']:
        assert chain['nodes']==sorted(chain['nodes'])
        assert chain['nodes'][-1]==chain['gain_node']
        for node,ancestor in zip(chain['nodes'][1:],chain['nodes']):
            assert a['records'][node-1]['parent_node']==ancestor
        assert len(chain['spectra'])==len(chain['operators'])==len(chain['nodes'])
    assert json.loads(json.dumps(a))==a
    jsonschema.validate(a,json.loads((ROOT/'docs/schemas/result-v0.3.schema.json').read_text(encoding='utf-8')))
    for strategy in ('random','resource','v02','mixed'):
        other=run_malignant_search(code,MemoryConfig(2,'Z'),replace(config,strategy=strategy))
        assert other['initial_population_ids']==a['initial_population_ids']
        assert other['evaluation_slots']==9

def test_configuration_bounds():
    with pytest.raises(ValueError):MalignantConfig(protected_slots=20)
    with pytest.raises(ValueError):MalignantConfig(compound_depth=0)
    with pytest.raises(ValueError):MalignantConfig(equivalence='magic')

def test_v03_cli_frontier_and_incompatible_model(tmp_path):
    from ftqec.cli import main
    source=tmp_path/'search.json';target=tmp_path/'frontier.json'
    result=run_malignant_search(circuit().code,MemoryConfig(2,'Z'),MalignantConfig(budget=3,max_weight=2,target_dc=2))
    source.write_text(json.dumps(result),encoding='utf-8')
    main(['frontier',str(source),'-o',str(target)])
    assert any(json.loads(target.read_text(encoding='utf-8')).values())
    with pytest.raises(SystemExit):
        main(['search',str(ROOT/'benchmarks/development/css4.json'),'--model','ideal-boundary','--strategy','v03'])
