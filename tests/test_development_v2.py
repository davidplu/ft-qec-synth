"""Independent benchmark tooling checks; the frozen algorithm is untouched."""
import importlib.util
from pathlib import Path
import sys

path=Path(__file__).resolve().parents[1]/'experiments/development_v2.py'
spec=importlib.util.spec_from_file_location('development_v2',path)
dv=importlib.util.module_from_spec(spec);spec.loader.exec_module(dv)
sys.path.insert(0,str(path.parent))
import compare_development_v2 as comparison

def test_generic_constructions_and_terminal_distance():
    for gs,n,k,d in ((dv.shor(3,3),9,1,3),(dv.grid(3),9,1,3)):
        code=dv.StabilizerCode.from_dict({'generators':gs})
        assert (code.n,code.k)==(n,k)
        assert dv.exact_code_distance(code)['distance']==d
        for basis in ('X','Z'):
            ceiling=dv.terminal_ceiling(code,basis)
            assert ceiling['status']=='EXACT_TERMINAL_ONLY'
            assert ceiling['distance']==3
            assert ceiling['full_circuit_lower_bound'] is False

def test_noncss_generator_control_preserves_distance_and_group():
    gs=dv.shor(3,3);a=dv.StabilizerCode.from_dict({'generators':gs})
    b=dv.StabilizerCode.from_dict({'generators':dv.mixed_generators(gs)})
    assert a.k==b.k==1
    assert any(p.x and p.z for p in b.generators)
    assert all(a.is_stabilizer(p) for p in b.generators)
    assert dv.exact_code_distance(b)['distance']==3

def test_seed_block_statistics_and_memory():
    assert comparison.sign_permutation([1]*10)==2/1024
    assert comparison.sign_permutation([0]*10)==1
    rows=[{'p':.01},{'p':.03},{'p':.9}];comparison.holm(rows)
    assert [r['p_holm'] for r in rows]==[.03,.06,.9]
    assert comparison.rss().get('peak_working_set_bytes',1)>0
