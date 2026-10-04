from dataclasses import dataclass
from hashlib import sha256
import json
from .pauli import Pauli
from .symplectic import echelon, reduce_vector

@dataclass(frozen=True)
class StabilizerCode:
    n: int
    generators: tuple
    name: str = "anonymous"

    def __post_init__(self):
        if self.n < 1: raise ValueError("n must be positive")
        if any(p.n != self.n for p in self.generators): raise ValueError("Inconsistent lengths")
        if any(a.symplectic(b) for a in self.generators for b in self.generators):
            raise ValueError("Generators do not commute")
        # Inputs use +1 Hermitian Paulis. Reject a hidden -I relation.
        phase_basis = {}
        for p in self.generators:
            x,z,phase = p.x,p.z,(p.x & p.z).bit_count()%4
            while x or z:
                pivot = (x | (z << self.n)).bit_length()-1
                if pivot not in phase_basis:
                    phase_basis[pivot] = (x,z,phase); break
                bx,bz,bp = phase_basis[pivot]
                phase = (phase + bp + 2*(z & bx).bit_count())%4
                x ^= bx; z ^= bz
            else:
                if phase: raise ValueError("Generators imply -I")

    @classmethod
    def from_dict(cls, d):
        g = tuple(Pauli.parse(s) for s in d['generators'])
        return cls(d.get('n', g[0].n if g else 0), g, d.get('name','anonymous'))
    def to_dict(self): return dict(n=self.n, generators=list(map(str,self.generators)), name=self.name)
    @property
    def basis(self): return echelon(p.packed for p in self.generators)
    @property
    def rank(self): return len(self.basis)
    @property
    def k(self): return self.n-self.rank
    @property
    def input_hash(self):
        return sha256(json.dumps(self.to_dict(),sort_keys=True).encode()).hexdigest()
    def syndrome(self,p): return sum(g.symplectic(p) << i for i,g in enumerate(self.generators))
    def is_stabilizer(self,p): return reduce_vector(p.packed,self.basis)==0
    def metrics(self):
        supports = [p.x|p.z for p in self.generators]
        return dict(n=self.n,rank=self.rank,k=self.k,commuting=True,
                    weights=[p.weight for p in self.generators],
                    degrees=[sum(s >> q & 1 for s in supports) for q in range(self.n)],
                    overlaps=[[(a&b).bit_count() for b in supports] for a in supports])
