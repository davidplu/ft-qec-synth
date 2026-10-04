from .pauli import Pauli
from .symplectic import nullspace, echelon, reduce_vector

def logical_basis(code):
    constraints = [p.z | (p.x << code.n) for p in code.generators]
    span = dict(code.basis)
    quotient = []
    for v in nullspace(constraints,2*code.n):
        if reduce_vector(v,span):
            quotient.append(Pauli.unpack(code.n,v))
            span = echelon(list(span.values())+[v])
    pairs = []
    while quotient:
        a = quotient.pop(0)
        j = next((i for i,b in enumerate(quotient) if a.symplectic(b)),None)
        if j is None: raise ArithmeticError("Degenerate logical quotient")
        b = quotient.pop(j)
        quotient = [v ^ (a if v.symplectic(b) else Pauli(code.n)) ^
                    (b if v.symplectic(a) else Pauli(code.n)) for v in quotient]
        pairs.append((a,b))
    if len(pairs)!=code.k: raise ArithmeticError("Incorrect logical dimension")
    return pairs

def logical_effect(error, pairs):
    return sum((error.symplectic(z) | (error.symplectic(x)<<1)) << (2*i)
               for i,(x,z) in enumerate(pairs))
