"""Independent boolean-array fault oracle and funnel regression checks."""
import unittest, random
from ftqec.codes.pauli import Pauli
from ftqec.codes.logicals import logical_basis, logical_effect
from ftqec.codes.stabilizer import StabilizerCode
from ftqec.architectures.generators import generate
from ftqec.circuits.extraction import build
from ftqec.circuits.model import Circuit
from ftqec.faults.signatures import signatures
from ftqec.search.engine import evaluate, search
from ftqec.scheduling.scheduler import schedule

# Independent representation and simultaneous-fault simulation.
def boolean_oracle(c, faults):
    x=[False]*c.num_qubits; z=[False]*c.num_qubits; records={}
    def inject(f):
        for q,p in zip(f.qubits,f.label):
            if p in 'XY': x[q]=not x[q]
            if p in 'YZ': z[q]=not z[q]
    for i,op in enumerate(c.operations):
        at=[f for f in faults if f.operation==i]
        for f in at:
            if f.before: inject(f)
        g=op.gate; a=op.qubits[0] if op.qubits else 0
        if g in ('PREP','RESET'): x[a]=z[a]=False
        elif g=='M':
            if op.record: records[op.record]=int(x[a])^int(any(f.kind=='measurement' for f in at))
        elif g=='H': x[a],z[a]=z[a],x[a]
        elif g in ('S','SDG'): z[a]^=x[a]
        elif g=='CX': b=op.qubits[1]; x[b]^=x[a]; z[a]^=z[b]
        elif g=='CZ': b=op.qubits[1]; z[a]^=x[b]; z[b]^=x[a]
        elif g=='SWAP':
            b=op.qubits[1]; x[a],x[b]=x[b],x[a]; z[a],z[b]=z[b],z[a]
        for f in at:
            if not f.before and f.kind!='measurement': inject(f)
    for f in faults:
        if f.operation==len(c.operations): inject(f)
    p=Pauli(c.code.n,sum(int(x[q])<<q for q in range(c.code.n)),sum(int(z[q])<<q for q in range(c.code.n)))
    d=sum((sum(records.get(r,0) for r in detector)&1)<<i for i,detector in enumerate(c.detectors))
    d |= c.code.syndrome(p)<<len(c.detectors)
    logical=logical_effect(p,logical_basis(c.code))
    logical |= sum((sum(records.get(r,0) for r in obs)&1)<<(2*c.code.k+i) for i,obs in enumerate(c.observables))
    flags=sum(records.get(r,0)<<i for i,r in enumerate(sorted(r for r in records if r.startswith('f'))))
    return d,logical,flags,p.packed

class IndependentTests(unittest.TestCase):
    def test_multifault_linearity_and_idle_signatures(self):
        code=StabilizerCode.from_dict({'generators':['YXXY','ZYYZ']})
        rng=random.Random(66)
        for candidate in generate(code,6,19):
            c=build(code,candidate); ss=signatures(c,True)
            for _ in range(100):
                group=rng.sample(ss,rng.randint(1,3))
                if len({s.fault.location for s in group})!=len(group): continue
                expected=[0,0,0,0]
                for s in group:
                    for i,v in enumerate((s.detectors,s.logical,s.flags,s.data)): expected[i]^=v
                self.assertEqual(tuple(expected),boolean_oracle(c,[s.fault for s in group]))
    def test_acceptance_threshold(self):
        code=StabilizerCode.from_dict({'generators':['XZZXI','IXZZX','XIXZZ','ZXIXZ']})
        candidate=next(generate(code,1))
        loose=evaluate(code,candidate,required_distance=2)
        strict=evaluate(code,candidate,required_distance=3)
        self.assertIsNone(loose['rejection']); self.assertEqual(strict['rejection'],'C_logical_witness')
    def test_stage_a_pruning_and_d_completion(self):
        code=StabilizerCode.from_dict({'generators':['ZI','IZ']})
        results=search(code,12,8,3,100000)
        self.assertTrue(any(r['stage']=='D' and r['bounds']['excluded_through']==3 for r in results['records']))
        self.assertTrue(any(r['rejection']=='A_resource_dominated' for r in results['records']))
    def test_barrier(self):
        c=Circuit(StabilizerCode(2,()),(),()); c.add('H',[0]); c.add('H',[0]); c.add('H',[1])
        c.add('BARRIER',[0,1]); c.add('M',[1],record='m')
        s=schedule(c); self.assertEqual(s.starts,[0,1,0,2,2]); self.assertEqual(s.depth,3)
    def test_schema_results(self):
        import jsonschema
        from pathlib import Path
        import json
        root=Path(__file__).resolve().parents[1]
        schema=json.loads((root/'docs/schemas/result.schema.json').read_text())
        c=StabilizerCode.from_dict({'generators':['ZZ']})
        jsonschema.validate(search(c,4,0),schema)

if __name__=='__main__': unittest.main()
