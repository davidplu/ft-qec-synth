from ..scheduling.scheduler import schedule

def resources(c):
    s=schedule(c); ops=c.operations
    return dict(data_qubits=c.code.n,syndrome_ancillas=len(c.syndrome_qubits),flag_ancillas=len(c.flag_qubits),
                Q=c.num_qubits,one_q_gates=sum(o.gate in ('H','S','SDG','X','Y','Z') for o in ops),
                two_q_gates=sum(o.gate in ('CX','CZ','SWAP') for o in ops),
                measurements=sum(o.gate=='M' for o in ops),resets=sum(o.gate=='RESET' for o in ops),
                preparations=sum(o.gate=='PREP' for o in ops),operation_count=sum(o.gate!='BARRIER' for o in ops),
                D=s.depth,QD=c.num_qubits*s.depth,depth_lower_bound=s.lower_bound,schedule_efficiency=s.efficiency)
