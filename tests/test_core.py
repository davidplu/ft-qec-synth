import unittest, itertools, random, json
from ftqec.codes.pauli import Pauli
from ftqec.codes.stabilizer import StabilizerCode
from ftqec.codes.symplectic import rank, nullspace
from ftqec.codes.logicals import logical_basis
from ftqec.certification.distance import exact_code_distance
from ftqec.circuits.model import Circuit
from ftqec.circuits.extraction import build
from ftqec.architectures.candidate import Candidate
from ftqec.architectures.generators import generate
from ftqec.scheduling.scheduler import schedule
from ftqec.evaluation.resources import resources
from ftqec.evaluation.pareto import frontier
from ftqec.faults.propagation import conjugate, propagate
from ftqec.faults.signatures import signatures, Fault
from ftqec.faults.search import search_faults
from ftqec.search.engine import search
from ftqec.search.mutations import mutate
from ftqec.hardware.graph import HardwareGraph
from ftqec.hardware.routing import validate_mapping
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
def development():
    return [StabilizerCode.from_dict(json.loads(p.read_text())) for p in sorted((ROOT/'benchmarks/development').glob('*.json'))]

class AlgebraTests(unittest.TestCase):
    def test_roundtrip_exhaustive(self):
        for n in range(1,5):
            for ps in itertools.product('IXYZ',repeat=n):
                text=''.join(ps); p=Pauli.parse(text)
                self.assertEqual(str(p),text); self.assertEqual(Pauli.unpack(n,p.packed),p)
                self.assertEqual(Pauli.from_vector(p.to_vector()),p)
    def test_commutation_independent(self):
        for a in itertools.product('IXYZ',repeat=3):
            for b in itertools.product('IXYZ',repeat=3):
                expected=sum(x!=y and x!='I' and y!='I' for x,y in zip(a,b))%2
                self.assertEqual(Pauli.parse(''.join(a)).symplectic(Pauli.parse(''.join(b))),expected)
    def test_rank_and_nullspace(self):
        rng=random.Random(3)
        for width in range(1,9):
            for _ in range(12):
                rows=[rng.randrange(1<<width) for _ in range(6)]; ns=nullspace(rows,width)
                self.assertEqual(len(ns),width-rank(rows))
                self.assertTrue(all((r&v).bit_count()%2==0 for r in rows for v in ns))
                self.assertEqual(rank(ns),len(ns))
    def test_metrics(self):
        c=StabilizerCode.from_dict({'generators':['ZZI','IZZ','ZIZ']})
        self.assertEqual((c.n,c.rank,c.k),(3,2,1))
        self.assertEqual(c.metrics()['degrees'],[2,2,2])
        self.assertEqual(c.metrics()['overlaps'],[[2,1,1],[1,2,1],[1,1,2]])
        for bad in [{'generators':['X','Z']},{'generators':['XX','ZZ','YY']},{'generators':['XQ']}]:
            with self.assertRaises(ValueError): StabilizerCode.from_dict(bad)
        self.assertEqual(StabilizerCode.from_dict({'generators':['XX','XX']}).rank,1)
    def test_logicals_general(self):
        codes=development()+[StabilizerCode(5,()),StabilizerCode.from_dict({'generators':['ZI','IZ']})]
        for c in codes:
            pairs=logical_basis(c); self.assertEqual(len(pairs),c.k)
            for i,(x,z) in enumerate(pairs):
                self.assertFalse(c.syndrome(x)); self.assertFalse(c.syndrome(z))
                self.assertFalse(c.is_stabilizer(x)); self.assertEqual(x.symplectic(z),1)
                for j,(a,b) in enumerate(pairs):
                    self.assertEqual(x.symplectic(a),0); self.assertEqual(z.symplectic(b),0)
                    self.assertEqual(x.symplectic(b),int(i==j))
    def test_distance(self):
        expected={'Three-qubit repetition':1,'Five-qubit perfect code':3,'Steane CSS':3,'Four-qubit CSS':2}
        for c in development():
            if c.name in expected: self.assertEqual(exact_code_distance(c)['distance'],expected[c.name])
        self.assertEqual(exact_code_distance(development()[0],0)['status'],'LOWER_BOUND')
    def test_arbitrary_n(self):
        c=StabilizerCode(100,(Pauli(100,0,3),))
        self.assertEqual(c.k,99); self.assertEqual(len(logical_basis(c)),99)

class CircuitTests(unittest.TestCase):
    def test_determinism_and_roundtrip(self):
        for c in development():
            a=list(generate(c,12,42)); b=list(generate(c,12,42))
            self.assertEqual(a,b); self.assertEqual(len({x.id for x in a}),12)
            for candidate in a:
                self.assertEqual(candidate,Candidate.from_dict(json.loads(json.dumps(candidate.to_dict()))))
                circuit=build(c,candidate)
                self.assertEqual(circuit.to_dict(),Circuit.from_dict(circuit.to_dict()).to_dict())
    def test_mutations_valid(self):
        rng=random.Random(13)
        for c in development():
            candidate=next(generate(c,1))
            for _ in range(80):
                candidate=mutate(candidate,rng); candidate.validate(c); build(c,candidate).validate()
    def test_scheduler(self):
        for code in development():
            for candidate in generate(code,8,7):
                c=build(code,candidate); s=schedule(c); occupied=set()
                for i,o in enumerate(c.operations):
                    for d in o.deps: self.assertGreaterEqual(s.starts[i],s.starts[d]+int(c.operations[d].gate!='BARRIER'))
                    if o.gate!='BARRIER':
                        for q in o.qubits:
                            self.assertNotIn((q,s.starts[i]),occupied); occupied.add((q,s.starts[i]))
                self.assertLessEqual(s.lower_bound,s.depth)
                self.assertGreater(s.efficiency,0)
    def test_resource_counts(self):
        code=StabilizerCode.from_dict({'generators':['ZZ']}); c=build(code,next(generate(code,1)))
        r=resources(c)
        self.assertEqual((r['Q'],r['one_q_gates'],r['two_q_gates'],r['measurements'],r['resets'],r['D']),(3,2,2,1,1,6))
        self.assertEqual(r['operation_count'],6); self.assertEqual(r['QD'],18)
    def test_invalid_ir(self):
        c=Circuit(StabilizerCode(1,()),(),()); c.add('CX',[0,0])
        with self.assertRaises(ValueError): c.validate()
        c.operations=[]; c.add('H',[0],deps=[0])
        with self.assertRaises(ValueError): c.validate()
    def test_hardware(self):
        code=StabilizerCode.from_dict({'generators':['ZZ']}); c=build(code,next(generate(code,1)))
        g=HardwareGraph((0,1,2),((0,2),(1,2)))
        self.assertTrue(validate_mapping(c,g,{0:0,1:1,2:2}))
        self.assertFalse(validate_mapping(c,HardwareGraph((0,1,2),((0,1),)),{0:0,1:1,2:2}))

# Independent dense complex matrix oracle, requiring no external simulator.
def matrix_pauli(p):
    size=1<<p.n; m=[[0j]*size for _ in range(size)]
    for col in range(size):
        phase=1j**((p.x&p.z).bit_count()) * (-1)**((p.z&col).bit_count())
        m[col^p.x][col]=phase
    return m

def unitary(g,n,qs):
    size=1<<n; m=[[0j]*size for _ in range(size)]; a=qs[0]
    for col in range(size):
        if g=='H':
            m[col & ~(1<<a)][col]=2**-.5
            m[col | (1<<a)][col]=(-1 if col>>a&1 else 1)*2**-.5
        elif g in ('S','SDG'): m[col][col]=(1j if g=='S' else -1j)**(col>>a&1)
        elif g=='CX': m[col^((col>>a&1)<<qs[1])][col]=1
        elif g=='CZ': m[col][col]=(-1)**((col>>a&1)*(col>>qs[1]&1))
        elif g=='SWAP':
            row=col
            if ((col>>a)^(col>>qs[1]))&1: row^=(1<<a)|(1<<qs[1])
            m[row][col]=1
    return m

def multiply(a,b): return [[sum(x*y for x,y in zip(row,col)) for col in zip(*b)] for row in a]
def adjoint(a): return [[x.conjugate() for x in col] for col in zip(*a)]

class PropagationTests(unittest.TestCase):
    def test_all_cliffords_against_dense_oracle(self):
        for gate,qs in [('H',(0,)),('S',(1,)),('SDG',(0,)),('CX',(0,1)),('CX',(1,0)),('CZ',(0,1)),('SWAP',(0,1))]:
            u=unitary(gate,2,qs)
            for text in map(''.join,itertools.product('IXYZ',repeat=2)):
                p=Pauli.parse(text); got=matrix_pauli(conjugate(p,gate,qs)); actual=multiply(multiply(u,matrix_pauli(p)),adjoint(u))
                self.assertTrue(any(all(abs(actual[i][j]-sign*got[i][j])<1e-9 for i in range(4) for j in range(4)) for sign in (1,-1)))
    def test_measurement_and_reset(self):
        c=Circuit(StabilizerCode(1,()),(),())
        c.add('IDLE',[0]); c.add('M',[0],record='r'); c.add('RESET',[0]); c.add('M',[0],record='s')
        err,records=propagate(c,Fault(0,(0,),'X','idle','op:0'))
        self.assertEqual(records,{'r':1,'s':0}); self.assertEqual(err.weight,0)
        err,records=propagate(c,Fault(1,(0,),'I','measurement','op:1'))
        self.assertEqual(records['r'],1); self.assertEqual(err.weight,0)
        err,records=propagate(c,Fault(2,(0,),'X','reset','op:2'))
        self.assertEqual(records['s'],1); self.assertEqual(str(err),'X')
    def test_signature_manual_hook(self):
        code=StabilizerCode.from_dict({'generators':['XXX']}); c=build(code,next(generate(code,1)))
        f=Fault(1,(3,),'X','h','op:1'); err,rec=propagate(c,f)
        self.assertEqual(str(err),'XXX'); self.assertEqual(rec['s0'],0)
    def test_flags_and_segments_noiseless_unitary(self):
        # Compare full pre-measurement unitary action to controlled-P, flags zero.
        code=StabilizerCode.from_dict({'generators':['YX']})
        candidate=Candidate(('YX',),((0,1),),(((0,2),),),(0,),(0,),1,1)
        c=build(code,candidate)
        # Ideal initial ancilla/reset state: arbitrary computational data basis.
        for data in range(4):
            state=[0j]*16; state[data]=1
            for op in c.operations:
                if op.gate in ('RESET','M'): continue
                u=unitary(op.gate,4,op.qubits)
                state=[sum(a*b for a,b in zip(row,state)) for row in u]
            self.assertTrue(all(abs(state[i])<1e-9 for i in range(16) if i>>3&1))
            p=matrix_pauli(Pauli.parse('YX'))
            for syn in (0,1):
                for row in range(4):
                    expected=((1 if row==data else 0)+(-1)**syn*p[row][data])/2
                    self.assertAlmostEqual(abs(state[row|(syn<<2)]-expected),0,places=9)
    def test_signature_search_vs_bruteforce(self):
        code=StabilizerCode.from_dict({'generators':['XXXX','ZZZZ']}); c=Circuit(code,(),())
        for q in range(code.n): c.add('IDLE',[q])
        ss=signatures(c)
        for weight in (1,2,3):
            answer=search_faults(c,ss,weight,10000000)
            brute=None
            for w in range(1,weight+1):
                for group in itertools.combinations(ss,w):
                    if len({s.fault.location for s in group})!=w: continue
                    d=l=0
                    for s in group: d^=s.detection; l^=s.logical
                    if d==0 and l: brute=w; break
                if brute: break
            self.assertEqual(answer['upper_bound'],brute)
            if brute is None: self.assertEqual(answer['excluded_through'],weight)
    def test_known_distance_and_witness(self):
        c=Circuit(StabilizerCode(1,()),(),()); c.add('IDLE',[0])
        out=search_faults(c,signatures(c),3)
        self.assertEqual(out['status'],'EXACT'); self.assertEqual(out['upper_bound'],1)
        self.assertEqual(out['witness']['detector_outcomes'],0)
        # Detect X and Z individually, but two storage faults can form XX logical.
        code=StabilizerCode.from_dict({'generators':['ZZ']}); c=Circuit(code,(),())
        c.add('IDLE',[0]); c.add('IDLE',[1])
        # Z is itself logical so distance one, correctly detected by basis projection.
        self.assertEqual(search_faults(c,signatures(c),2)['upper_bound'],1)
    def test_weight_two_and_three_exact(self):
        for name,expected in [('css4',2),('steane',3)]:
            code=StabilizerCode.from_dict(json.loads((ROOT/f'benchmarks/development/{name}.json').read_text()))
            c=Circuit(code,(),())
            for q in range(code.n): c.add('IDLE',[q])
            out=search_faults(c,signatures(c),3,1000000)
            self.assertEqual(out['status'],'EXACT'); self.assertEqual(out['upper_bound'],expected)
            self.assertEqual(out['witness']['fault_count'],expected)
            self.assertEqual(out['witness']['detector_outcomes'],0)
            self.assertTrue(out['witness']['logical_coset'])
            self.assertEqual(len({f['location'] for f in out['witness']['faults']}),expected)
    def test_pair_location_exclusion(self):
        from ftqec.faults.signatures import Signature
        c=Circuit(StabilizerCode(1,()),(),()); c.add('IDLE',[0])
        ss=[Signature(Fault(0,(0,),'X','idle','same'),1,0,1,1),
            Signature(Fault(0,(0,),'Z','idle','same'),1,0,2,2)]
        out=search_faults(c,ss,3)
        self.assertIsNone(out['witness']); self.assertEqual(out['excluded_through'],3)
    def test_capped_triples_keep_only_completed_bounds(self):
        code=StabilizerCode.from_dict(json.loads((ROOT/'benchmarks/development/steane.json').read_text()))
        c=Circuit(code,(),())
        for q in range(code.n): c.add('IDLE',[q])
        ss=signatures(c)
        pair=search_faults(c,ss,2)
        triple=search_faults(c,ss,3,pair['combinations_examined'])
        self.assertEqual(triple['reason'],'work_limit'); self.assertEqual(triple['excluded_through'],2)
    def test_detector_and_observable_parity(self):
        c=Circuit(StabilizerCode(1,()),(),()); c.add('IDLE',[0]); c.add('M',[0],record='r')
        c.detectors=[['r']]; c.observables=[['r']]
        ss=signatures(c); flip=next(s for s in ss if s.fault.kind=='measurement')
        self.assertEqual(flip.detectors,1); self.assertEqual(flip.logical,4)
    def test_exhaustion_not_certified(self):
        c=build(development()[0],next(generate(development()[0],1)))
        out=search_faults(c,signatures(c),3,0)
        self.assertEqual(out['status'],'UNRESOLVED'); self.assertEqual(out['excluded_through'],0)
    def test_idle_locations(self):
        c=build(development()[0],next(generate(development()[0],1)))
        ss=signatures(c,True)
        self.assertGreater(len(ss),len(signatures(c)))
        self.assertTrue(any(s.fault.kind=='idle' for s in ss))

class IntegrationTests(unittest.TestCase):
    def test_reproducible_search(self):
        c=development()[0]; a=search(c,8,5,2,100000); b=search(c,8,5,2,100000)
        for run in (a,b):
            run.pop('runtime_seconds')
            for record in run['records']+run['frontier']+run['exploratory_frontier']:
                for key in ('runtime_seconds','signature_seconds','fault_search_seconds'): record.pop(key,None)
        self.assertEqual(a,b)
    def test_pareto(self):
        def r(q,d,lb): return {'resources':dict(Q=q,D=d,QD=q*d,two_q_gates=10),'bounds':dict(lower_bound=lb)}
        a,b,c=r(4,4,2),r(5,5,2),r(6,6,3)
        self.assertEqual(frontier([a,b,c]),[a,c])
    def test_cli(self):
        from ftqec.cli import main
        import tempfile
        with tempfile.TemporaryDirectory(dir=ROOT) as folder:
            dest=Path(folder)/'result.json'
            main(['search',str(ROOT/'benchmarks/development/css4.json'),'--budget','4','--output',str(dest)])
            d=json.loads(dest.read_text()); self.assertEqual(d['candidates_evaluated'],4)
            main(['frontier',str(dest),'--output',str(Path(folder)/'frontier.json')])

if __name__=='__main__': unittest.main()
