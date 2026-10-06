"""Generic logical-coordinate projection bounds with independent physical checks.

If D=0 implies every coordinate equals the selected logical bit, an undetected
logical flip has coordinate Hamming weight m. If every physical fault flips at
most a coordinates, XOR subadditivity gives distance >= ceil(m/a). Relations
and the per-fault bound are checked for EVERY legal physical singleton. This is
an exact lower bound, not an assumption about flag or cat correctness.
"""
from collections import Counter
from hashlib import sha256
import json,time
from ..circuits.model import Circuit
from ..codes.symplectic import echelon
from ..faults.signatures import enumerate_faults
from ..faults.batch_verification import singleton_effects
from ..resource_synthesis.certification import SignatureCache,fingerprint


def representatives(circuit,pool_limit=4096):
    if not circuit.observables or circuit.boundary_model!='repeated_noisy_memory':raise ValueError('Selected physical memory observable required')
    original=0
    for record in circuit.observables[0]:
        if not record.startswith('d') or not record[1:].isdigit():raise ValueError('Product data readout required')
        original^=1<<int(record[1:])
    stabilizers=[sum((p!='I')<<i for i,p in enumerate(row['pauli']))
                 for row in circuit.experiment['final_compatible_products']]
    basis=sorted(echelon(stabilizers).values());pool=[]
    for coefficient in range(min(1<<len(basis),pool_limit)):
        mask=original
        for i,row in enumerate(basis):
            if coefficient>>i&1:mask^=row
        pool.append(mask)
    selected=[];used=0
    for mask in sorted(set(pool),key=lambda x:(x.bit_count(),x)):
        if mask and not (mask&used):selected.append(mask);used|=mask
    return selected,len(pool)<(1<<len(basis))


def diagnostic(circuit,masks):
    c=Circuit.from_dict(circuit.to_dict());offset=len(c.observables)
    c.observables.extend([[f'd{i}' for i in range(c.code.n) if mask>>i&1] for mask in masks])
    return c,offset


def relations(effects,detectors,offset,count):
    rows=[0]*detectors;logical=0;coordinates=[0]*count
    for i,(d,l) in enumerate(effects):
        bit=1<<i
        while d:
            low=d&-d;rows[low.bit_length()-1]|=bit;d^=low
        if l&1:logical|=bit
        for j in range(count):
            if l>>(offset+j)&1:coordinates[j]|=bit
    basis={}
    for j,row in enumerate(rows):
        coefficients=1<<j
        while row:
            pivot=row.bit_length()-1
            if pivot in basis:
                b,c=basis[pivot];row^=b;coefficients^=c
            else:basis[pivot]=(row,coefficients);break
    combinations=[]
    for coordinate in coordinates:
        row=coordinate^logical;coefficients=0
        while row:
            pivot=row.bit_length()-1
            if pivot not in basis:return None
            b,c=basis[pivot];row^=b;coefficients^=c
        combinations.append(coefficients)
    return combinations


def certify(circuit,pool_limit=4096):
    if pool_limit<1:raise ValueError('Positive representative pool limit required')
    started=time.perf_counter();masks,truncated=representatives(circuit,pool_limit)
    c,offset=diagnostic(circuit,masks);ss,_=SignatureCache().get(c)
    effects=[(s.detectors,s.logical) for s in ss]
    combinations=relations(effects,len(circuit.detectors),offset,len(masks))
    if combinations is None:return dict(verified=False,reason='projection_relation_not_in_detector_span')
    norm=Counter((l>>offset).bit_count() for d,l in effects);maximum=max(norm,default=0)
    lower=(len(masks)+maximum-1)//maximum if maximum else None
    return dict(lower_bound=lower,algorithm='logical-packing-physical-projection-1',
        circuit_hash=fingerprint(circuit),fault_inventory_hash=sha256(json.dumps([s.fault.to_dict() for s in ss],sort_keys=True).encode()).hexdigest(),
        coordinate_masks=masks,detector_combinations=combinations,coordinate_count=len(masks),
        maximum_single_fault_coordinate_weight=maximum,single_fault_weight_histogram=dict(norm),
        representative_pool_limit=pool_limit,representative_pool_truncated=truncated,
        physical_variants=len(ss),runtime_seconds=time.perf_counter()-started,
        scope='first selected product-readout logical observable; no all-logical-channel claim',
        proof='D=0 forces all coordinates=L; Hamming XOR subadditivity and exhaustive singleton norm bound')


def verify(circuit,certificate):
    started=time.perf_counter()
    if fingerprint(circuit)!=certificate['circuit_hash']:return dict(verified=False,reason='circuit_hash')
    faults=list(enumerate_faults(circuit,False))
    inventory=sha256(json.dumps([f.to_dict() for f in faults],sort_keys=True).encode()).hexdigest()
    if inventory!=certificate['fault_inventory_hash']:return dict(verified=False,reason='fault_inventory_hash')
    masks=certificate['coordinate_masks'];combinations=certificate['detector_combinations']
    if len(masks)!=len(combinations) or not masks:return dict(verified=False,reason='coordinate_payload')
    if certificate['coordinate_count']!=len(masks) or any(mask<1 or mask>>circuit.code.n for mask in masks):
        return dict(verified=False,reason='coordinate_payload')
    if any(combination<0 or combination>>len(circuit.detectors) for combination in combinations):
        return dict(verified=False,reason='detector_payload')
    declared=certificate['maximum_single_fault_coordinate_weight']
    if declared<1 or not 1<=certificate['lower_bound']<=(len(masks)+declared-1)//declared:
        return dict(verified=False,reason='lower_bound')
    c,offset=diagnostic(circuit,masks);effects=singleton_effects(c,faults);maximum=0
    for d,l in effects:
        coordinate=l>>offset;maximum=max(maximum,coordinate.bit_count())
        for j,combination in enumerate(combinations):
            if ((d&combination).bit_count()&1)!=(((coordinate>>j)&1)^(l&1)):
                return dict(verified=False,reason='detector_relation')
    if maximum>certificate['maximum_single_fault_coordinate_weight']:return dict(verified=False,reason='single_fault_norm')
    bound=(len(masks)+maximum-1)//maximum if maximum else None
    if bound is None or certificate['lower_bound']>bound:return dict(verified=False,reason='lower_bound')
    return dict(verified=True,lower_bound=certificate['lower_bound'],singleton_replays=len(faults),
        coordinate_count=len(masks),maximum_single_fault_coordinate_weight=maximum,
        method='independent_forward_physical_projection_relations',runtime_seconds=time.perf_counter()-started)
