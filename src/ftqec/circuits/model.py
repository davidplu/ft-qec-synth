from dataclasses import dataclass, field, asdict
from ..codes.stabilizer import StabilizerCode
from ..serialization import json_native

ARITY = {'H':1,'S':1,'SDG':1,'X':1,'Y':1,'Z':1,'CX':2,'CZ':2,'SWAP':2,
         'PREP':1,'RESET':1,'M':1,'IDLE':1,'BARRIER':None}

@dataclass(frozen=True)
class Operation:
    gate: str
    qubits: tuple
    deps: tuple = ()
    record: str | None = None
    check: int | None = None
    round_index: int | None = None
    role: str | None = None
    interval: int | None = None
    interaction_position: int | None = None

@dataclass
class Circuit:
    code: StabilizerCode
    syndrome_qubits: tuple
    flag_qubits: tuple
    operations: list = field(default_factory=list)
    detectors: list = field(default_factory=list)
    observables: list = field(default_factory=list)
    boundary_model: str = 'ideal_initial_and_final_syndrome'
    experiment: dict = field(default_factory=dict)

    @property
    def num_qubits(self): return self.code.n+len(self.syndrome_qubits)+len(self.flag_qubits)
    def add(self,gate,qubits,deps=(),record=None,check=None,**metadata):
        self.operations.append(Operation(gate,tuple(qubits),tuple(deps),record,check,**metadata))
        return len(self.operations)-1
    def validate(self):
        allq = tuple(range(self.code.n))+self.syndrome_qubits+self.flag_qubits
        if sorted(allq)!=list(range(self.num_qubits)): raise ValueError('Qubit allocation invalid')
        records = set()
        for i,op in enumerate(self.operations):
            if op.gate not in ARITY: raise ValueError('Unsupported gate')
            if ARITY[op.gate] is not None and len(op.qubits)!=ARITY[op.gate]: raise ValueError('Gate arity')
            if len(set(op.qubits))!=len(op.qubits) or any(q not in allq for q in op.qubits): raise ValueError('Invalid qubits')
            if any(d<0 or d>=i for d in op.deps): raise ValueError('Dependencies must point backwards')
            if op.record:
                if op.gate!='M' or op.record in records: raise ValueError('Invalid measurement record')
                records.add(op.record)
        if self.boundary_model not in ('ideal_initial_and_final_syndrome','repeated_noisy_memory'): raise ValueError('Unsupported boundary model')
        if any(r not in records for d in self.detectors+self.observables for r in d): raise ValueError('Unknown record')
    def to_dict(self):
        return json_native(dict(code=self.code.to_dict(),syndrome_qubits=self.syndrome_qubits,flag_qubits=self.flag_qubits,
                    operations=[asdict(op) for op in self.operations],detectors=self.detectors,
                    observables=self.observables,boundary_model=self.boundary_model,experiment=self.experiment))
    @classmethod
    def from_dict(cls,d):
        c = cls(StabilizerCode.from_dict(d['code']),tuple(d['syndrome_qubits']),tuple(d['flag_qubits']))
        c.operations = [Operation(o['gate'],tuple(o['qubits']),tuple(o.get('deps',())),o.get('record'),o.get('check'),o.get('round_index'),o.get('role'),o.get('interval'),o.get('interaction_position')) for o in d['operations']]
        c.detectors=d.get('detectors',[]); c.observables=d.get('observables',[])
        c.boundary_model=d.get('boundary_model','ideal_initial_and_final_syndrome'); c.experiment=d.get('experiment',{}); c.validate(); return c
