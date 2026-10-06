"""Delete only provably disconnected, unobserved ancillary components.

An unreferenced measurement on an ancilla that touched data is NOT orphaned:
its physical channel can matter. Such removal requires an ordinary noisy edit.
"""
from dataclasses import replace
from ..circuits.model import Circuit
from ..scheduling.scheduler import schedule


def disconnected_ancillas(circuit):
    referenced={r for row in circuit.detectors+circuit.observables for r in row}
    connected=set(range(circuit.code.n))
    for op in circuit.operations:
        if op.gate!='BARRIER' and op.record in referenced:connected.update(op.qubits)
    changed=True
    while changed:
        changed=False
        for op in circuit.operations:
            if op.gate=='BARRIER':continue
            if connected.intersection(op.qubits) and not set(op.qubits)<=connected:
                connected.update(op.qubits);changed=True
    removed=set(range(circuit.num_qubits))-connected
    c=Circuit.from_dict(circuit.to_dict());indices={};ops=[]
    remap={q:i for i,q in enumerate(sorted(connected))}
    for i,op in enumerate(c.operations):
        deps=set()
        for j in op.deps:deps.update(indices[j])
        if op.gate!='BARRIER' and set(op.qubits)<=removed:
            indices[i]=deps;continue
        indices[i]={len(ops)}
        qs=tuple(range(len(connected))) if op.gate=='BARRIER' else tuple(remap[q] for q in op.qubits)
        ops.append(replace(op,qubits=qs,deps=tuple(sorted(deps))))
    c.operations=ops;c.syndrome_qubits=tuple(remap[q] for q in c.syndrome_qubits if q in connected)
    c.flag_qubits=tuple(remap[q] for q in c.flag_qubits if q in connected)
    c.validate();schedule(c)
    return c,dict(removed_qubits=sorted(removed),removed_operations=len(circuit.operations)-len(ops),
                  proof='deleted components are tensor-disconnected from data and all referenced records')
