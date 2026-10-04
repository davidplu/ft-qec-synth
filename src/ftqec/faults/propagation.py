from ..codes.pauli import Pauli

def conjugate(p,gate,qubits):
    x,z=p.x,p.z
    a=qubits[0] if qubits else 0; mask=1<<a
    if gate=='H':
        if ((x^z)>>a)&1: x^=mask; z^=mask
    elif gate in ('S','SDG'): z^=(x&mask)
    elif gate=='CX':
        b=qubits[1]
        x^=((x>>a)&1)<<b; z^=((z>>b)&1)<<a
    elif gate=='CZ':
        b=qubits[1]
        z^=((x>>a)&1)<<b; z^=((x>>b)&1)<<a
    elif gate=='SWAP':
        b=qubits[1]
        if ((x>>a)^(x>>b))&1: x^=(1<<a)|(1<<b)
        if ((z>>a)^(z>>b))&1: z^=(1<<a)|(1<<b)
    elif gate not in ('X','Y','Z','IDLE','BARRIER'): raise ValueError('Not a unitary Clifford')
    return Pauli(p.n,x,z)

def propagate(c,fault):
    error=Pauli(c.num_qubits); records={}
    for i,op in enumerate(c.operations):
        if fault.operation==i and fault.before: error ^= fault.pauli(c.num_qubits)
        if op.gate in ('RESET','PREP'):
            q=op.qubits[0]; mask=~(1<<q)
            error=Pauli(error.n,error.x&mask,error.z&mask)
        elif op.gate=='M':
            bit=(error.x>>op.qubits[0])&1
            if fault.operation==i and fault.kind=='measurement': bit^=1
            if op.record: records[op.record]=bit
        else: error=conjugate(error,op.gate,op.qubits)
        if fault.operation==i and not fault.before and fault.kind!='measurement': error^=fault.pauli(c.num_qubits)
    mask=(1<<c.code.n)-1
    return Pauli(c.code.n,error.x&mask,error.z&mask),records
