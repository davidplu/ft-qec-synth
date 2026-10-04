def append_gadget(c, check, order, intervals, ancilla, flags, dependencies=()):
    """Ancilla |+>, controlled-P data interactions, ancilla X readout.

    Flags are |0>, with paired ancilla->flag CX gates bracketing intervals.
    Each interval uses a fresh reset/measurement epoch; slots can be reused.
    """
    last = tuple(dependencies)
    def emit(g,qs,record=None,role=None,interval=None,position=None):
        nonlocal last
        i = c.add(g,qs,last,record,check,role=role,interval=interval,interaction_position=position); last=(i,); return i
    emit('RESET',[ancilla],role='syndrome_reset'); emit('H',[ancilla],role='syndrome_prepare')
    starts={}; ends={}
    for j,(lo,hi) in enumerate(intervals):
        starts.setdefault(lo,[]).append(j); ends.setdefault(hi,[]).append(j)
    text = str(c.code.generators[check])
    for pos in range(len(order)+1):
        for j in ends.get(pos,[]):
            f=flags[j]; emit('CX',[ancilla,f],role='flag_close',interval=j,position=pos)
            rec=f'f{check}_{j}'; emit('M',[f],rec,role='flag_readout',interval=j,position=pos); c.detectors.append([rec])
        for j in starts.get(pos,[]):
            f=flags[j]; emit('RESET',[f],role='flag_reset',interval=j,position=pos); emit('CX',[ancilla,f],role='flag_open',interval=j,position=pos)
        if pos==len(order): break
        q=order[pos]; p=text[q]
        if p=='X': emit('CX',[ancilla,q],role='data_interaction',position=pos)
        elif p=='Z': emit('CZ',[ancilla,q],role='data_interaction',position=pos)
        elif p=='Y':
            emit('SDG',[q],role='data_basis_before',position=pos); emit('CX',[ancilla,q],role='data_interaction',position=pos); emit('S',[q],role='data_basis_after',position=pos)
        else: raise ValueError('Order contains identity')
    emit('H',[ancilla],role='syndrome_basis_readout'); rec=f's{check}'; emit('M',[ancilla],rec,role='syndrome_readout')
    c.detectors.append([rec])
    return last[0]
