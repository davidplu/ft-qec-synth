def echelon(rows):
    basis = {}
    for row in rows:
        while row:
            pivot = row.bit_length()-1
            if pivot in basis: row ^= basis[pivot]
            else:
                basis[pivot] = row
                break
    return basis

def reduce_vector(row, basis):
    for p in sorted(basis, reverse=True):
        if row >> p & 1: row ^= basis[p]
    return row

def rank(rows): return len(echelon(rows))

def nullspace(rows, width):
    rows = list(rows)
    pivots = []
    r = 0
    for c in range(width):
        j = next((j for j in range(r,len(rows)) if rows[j] >> c & 1), None)
        if j is None: continue
        rows[r], rows[j] = rows[j], rows[r]
        for j in range(len(rows)):
            if j != r and rows[j] >> c & 1: rows[j] ^= rows[r]
        pivots.append(c)
        r += 1
    return [ (1 << c) | sum((1 << p) for j,p in enumerate(pivots) if rows[j] >> c & 1)
             for c in range(width) if c not in pivots ]
