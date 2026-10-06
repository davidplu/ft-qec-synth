"""Independent exclusions through weight four using physical pair representatives.

For a family of two-location sets, three mutually disjoint edges are a universal
representative against any forbidden set of size <=2. Otherwise a maximal
matching has <=2 edges; its <=4 vertices cover every edge. Keep up to three
distinct neighbors per cover vertex. This <=12-edge family preserves existence
of an edge disjoint from ANY forbidden set of size <=2. Re-kernelization is
transitive, so streaming physical pairs is exact and bounded per effect bucket.
"""
from collections import defaultdict
from itertools import combinations
from hashlib import sha256
import json,time
from ..faults.signatures import enumerate_faults
from ..faults.batch_verification import singleton_effects
from ..faults.verification import replay,verify_witness
from ..resource_synthesis.certification import fingerprint


def kernel(edges):
    unique={tuple(sorted((e[0],e[1]))):e for e in edges};edges=list(unique.values())
    covered=set();matching=[]
    for edge in edges:
        if edge[0] not in covered and edge[1] not in covered:
            matching.append(edge);covered.update(edge[:2])
            if len(matching)==3:return matching,True
    chosen={}
    for vertex in sorted(covered):
        neighbors=set()
        for edge in edges:
            if vertex not in edge[:2]:continue
            other=edge[1] if edge[0]==vertex else edge[0]
            if other in neighbors:continue
            neighbors.add(other);chosen[tuple(sorted(edge[:2]))]=edge
            if len(neighbors)==3:break
    return list(chosen.values()),False


def exclusion(circuit,through=4,work_limit=16000000,table_limit=500000):
    if not 0<=through<=4 or work_limit<0 or table_limit<1:raise ValueError('Unsupported exclusion limits')
    started=time.perf_counter();faults=list(enumerate_faults(circuit,False));effects=singleton_effects(circuit,faults)
    rows={};detector_groups=defaultdict(lambda:defaultdict(dict));work=0
    for i,(d,l) in enumerate(effects):
        detector_groups[d][l].setdefault(faults[i].location,i)
        if d or l:rows.setdefault((faults[i].location,d,l),i)
    def result(excluded,reason=None,indices=None):
        rec=dict(verified=indices is None and reason is None,excluded_through=excluded,
            reason=reason,work=work,physical_variants=len(faults),location_channels=len(rows),
            runtime_seconds=time.perf_counter()-started,algorithm='forward-physical-pair-kernel-1',
            circuit_hash=fingerprint(circuit),fault_inventory_hash=sha256(json.dumps([f.to_dict() for f in faults],sort_keys=True).encode()).hexdigest())
        if indices:
            chosen=[faults[i].to_dict() for i in indices];actual=replay(circuit.to_dict(),chosen)
            w=dict(fault_count=len(chosen),faults=chosen,**{k:actual[k] for k in
                ('detector_outcomes','flag_outcomes','logical_coset','final_data_pauli')})
            if not verify_witness(circuit.to_dict(),w)['verified']:raise ArithmeticError('Pair-audit witness replay failed')
            rec['witness']=w
        return rec
    if through>=1:
        for i,(d,l) in enumerate(effects):
            if not d and l:return result(0,indices=[i])
    if through>=2:
        for logicals in detector_groups.values():
            for a,b in combinations(logicals,2):
                for loc,i in logicals[a].items():
                    for other,j in logicals[b].items():
                        if loc!=other:return result(1,indices=[i,j])
    if through<=2:return result(through)
    channels=[(faults[i].operation,d,l,i) for (loc,d,l),i in rows.items()]
    pairs={}
    for offset,(a,da,la,ia) in enumerate(channels):
        for b,db,lb,ib in channels[offset+1:]:
            if a==b:continue
            if work>=work_limit:return result(2,'work_limit')
            work+=1;key=(da^db,la^lb);existing=pairs.get(key)
            if existing is None:
                if len(pairs)>=table_limit:return result(2,'table_limit')
                pairs[key]=([(a,b,ia,ib)],False)
            elif not existing[1]:pairs[key]=kernel(existing[0]+[(a,b,ia,ib)])
    # Number of logical coordinates is generally small; index by detector.
    indexed=defaultdict(dict)
    for (d,l),family in pairs.items():indexed[d][l]=family[0]
    for loc,d,l,i in channels:
        for pair_l,family in indexed.get(d,{}).items():
            if pair_l==l:continue
            for a,b,ia,ib in family:
                if work>=work_limit:return result(2,'work_limit')
                work+=1
                if loc not in (a,b):return result(2,indices=[i,ia,ib])
    if through==3:return {**result(3),'pair_effect_buckets':len(pairs)}
    for logicals in indexed.values():
        for a,b in combinations(logicals,2):
            for left in logicals[a]:
                for right in logicals[b]:
                    if work>=work_limit:return result(3,'work_limit')
                    work+=1
                    if set(left[:2]).isdisjoint(right[:2]):return result(3,indices=[left[2],left[3],right[2],right[3]])
    return {**result(4),'pair_effect_buckets':len(pairs),
        'pair_representatives':sum(len(v[0]) for v in pairs.values()),'per_bucket_maximum':12,
        'proof_payload':'complete physical channel pairs; <=12-edge representatives preserve every two-location forbidden set; rerun required'}
