"""Structural metadata, not strategy-outcome-based benchmark selection."""
from itertools import combinations,product
from development_v2 import OUT,ROOT,dump,code_for,Pauli,assert_frozen
import json,statistics

def main():
    assert_frozen();rows=json.loads((OUT/'candidate_pool.json').read_text());out=[]
    for row in rows:
        code=code_for(row);ws=[p.weight for p in code.generators];n=code.n
        shift=lambda p:Pauli(n,((p.x<<1)&((1<<n)-1))|(p.x>>(n-1)),((p.z<<1)&((1<<n)-1))|(p.z>>(n-1)))
        cyclic=all(code.is_stabilizer(shift(p)) for p in code.generators)
        cert=row['distance_certificate'];d=cert.get('construction_distance',cert.get('distance',cert.get('lower_bound')))
        witness=next((str(p) for p in code.generators if d and p.weight<d),None)
        # Only modest exhaustive degeneracy checks; large absence is unknown.
        if witness is None and d and d<=3 and n<=25:
            for w in range(1,d):
                for support in combinations(range(n),w):
                    for labels in product('XYZ',repeat=w):
                        a=['I']*n
                        for q,p in zip(support,labels):a[q]=p
                        p=Pauli.parse(''.join(a))
                        if code.is_stabilizer(p):witness=str(p);break
                    if witness:break
                if witness:break
            degeneration='DEGENERATE' if witness else 'NONDEGENERATE_BELOW_CERTIFIED_DISTANCE'
        else:degeneration='DEGENERATE' if witness else 'UNRESOLVED'
        supports=[p.x|p.z for p in code.generators];over=[(a&b).bit_count() for i,a in enumerate(supports) for b in supports[:i]]
        out.append({'name':row['name'],'cyclic_in_supplied_qubit_order':cyclic,'degeneracy':degeneration,
            'low_weight_stabilizer_witness':witness,'check_weights':sorted(set(ws)),
            'mean_overlap':statistics.mean(over) if over else 0,'max_overlap':max(over,default=0),
            'max_degree':max(code.metrics()['degrees']),
            'geometry':'grid-derived; dense variants include extended supports' if row['family']=='checkerboard_grid' else
                       'rectangular row-pair supports plus nearest-row Z pairs' if row['family']=='rectangular_shor' else 'algebraic nonlocal/no supplied hardware graph',
            'hardware_routing_performed':False})
    dump(OUT/'structural_diversity.json',out)

if __name__=='__main__':main()
