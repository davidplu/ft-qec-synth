def validate_mapping(circuit,graph,mapping):
    if set(mapping)!=set(range(circuit.num_qubits)) or len(set(mapping.values()))!=len(mapping):
        raise ValueError('Mapping must be injective and complete')
    if any(node not in graph.nodes for node in mapping.values()): raise ValueError('Unknown hardware node')
    return all(graph.allows(mapping[o.qubits[0]],mapping[o.qubits[1]]) for o in circuit.operations if len(o.qubits)==2)
