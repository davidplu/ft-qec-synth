def append_gadget(c, check, order, intervals, ancilla, flags, dependencies=()):
    """Ancilla |+>, controlled-P data interactions, ancilla X readout.

    Flags are |0>, with paired ancilla->flag CX gates bracketing intervals.
    Each interval uses a fresh reset/measurement epoch; slots can be reused.
    """
    last = tuple(dependencies)
    def emit(g,qs,record=None):
        nonlocal last
        i = c.add(g,qs,last,record,check); last=(i,); return i
    emit('RESET',[ancilla]); emit('H',[ancilla])
    starts={}; ends={}
    for j,(lo,hi) in enumerate(intervals):
        starts.setdefault(lo,[]).append(j); ends.setdefault(hi,[]).append(j)
    text = str(c.code.generators[check])
    for pos in range(len(order)+1):
        for j in ends.get(pos,[]):
            f=flags[j]; emit('CX',[ancilla,f])
            rec=f'f{check}_{j}'; emit('M',[f],rec); c.detectors.append([rec])
        for j in starts.get(pos,[]):
            f=flags[j]; emit('RESET',[f]); emit('CX',[ancilla,f])
        if pos==len(order): break
        q=order[pos]; p=text[q]
        if p=='X': emit('CX',[ancilla,q])
        elif p=='Z': emit('CZ',[ancilla,q])
        elif p=='Y':
            emit('SDG',[q]); emit('CX',[ancilla,q]); emit('S',[q])
        else: raise ValueError('Order contains identity')
    emit('H',[ancilla]); rec=f's{check}'; emit('M',[ancilla],rec)
    c.detectors.append([rec])
    return last[0]
