from dataclasses import dataclass

@dataclass(frozen=True)
class Pauli:
    n: int
    x: int = 0
    z: int = 0

    def __post_init__(self):
        if self.n < 0 or min(self.x, self.z) < 0 or (self.x | self.z) >> self.n:
            raise ValueError("Invalid Pauli masks")

    @classmethod
    def parse(cls, text):
        if any(p not in "IXYZ" for p in text):
            raise ValueError("Unsigned I/X/Y/Z strings required")
        return cls(len(text), sum(1 << i for i,p in enumerate(text) if p in "XY"),
                   sum(1 << i for i,p in enumerate(text) if p in "YZ"))

    def __str__(self):
        return "".join("IXZY"[((self.x >> i)&1) + 2*((self.z >> i)&1)] for i in range(self.n))

    def __xor__(self, other):
        if self.n != other.n: raise ValueError("Pauli lengths differ")
        return Pauli(self.n, self.x ^ other.x, self.z ^ other.z)

    def symplectic(self, other):
        if self.n != other.n: raise ValueError("Pauli lengths differ")
        return ((self.x & other.z).bit_count() + (self.z & other.x).bit_count()) & 1

    @property
    def weight(self): return (self.x | self.z).bit_count()
    @property
    def packed(self): return self.x | (self.z << self.n)
    def to_vector(self):
        """Return (x_0,...,x_n-1,z_0,...,z_n-1)."""
        return tuple((self.x >> q)&1 for q in range(self.n)) + tuple((self.z >> q)&1 for q in range(self.n))
    @classmethod
    def from_vector(cls, vector):
        bits=tuple(vector)
        if len(bits)%2 or any(b not in (0,1) for b in bits): raise ValueError('Even-length binary vector required')
        n=len(bits)//2
        return cls(n,sum(b<<q for q,b in enumerate(bits[:n])),sum(b<<q for q,b in enumerate(bits[n:])))
    @classmethod
    def unpack(cls, n, bits): return cls(n, bits & ((1 << n)-1), bits >> n)
