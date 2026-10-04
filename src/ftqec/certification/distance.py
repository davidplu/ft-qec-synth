from itertools import combinations, product
from ..codes.pauli import Pauli

def exact_code_distance(code, max_patterns=1000000):
    count = 0
    if code.k == 0: return dict(status="UNRESOLVED", reason="No encoded logical qubits")
    for w in range(1,code.n+1):
        for support in combinations(range(code.n),w):
            for labels in product("XYZ",repeat=w):
                count += 1
                if count > max_patterns: return dict(status="LOWER_BOUND",lower_bound=w,patterns=count-1)
                text = ['I']*code.n
                for q,p in zip(support,labels): text[q]=p
                p = Pauli.parse(''.join(text))
                if not code.syndrome(p) and not code.is_stabilizer(p):
                    return dict(status="EXACT",distance=w,witness=str(p),patterns=count)
