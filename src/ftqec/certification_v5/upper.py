"""Cheap upper witnesses from physical readout-nullspace cosets; never a lower proof."""
from itertools import combinations
from ..codes.symplectic import nullspace
from ..faults.search import witness
from ..faults.verification import verify_witness


def terminal_witness(circuit,signatures,pair_limit=4096):
    terminal=[s for s in signatures if s.fault.kind=='measurement' and
              circuit.operations[s.fault.operation].role=='final_data_readout']
    rows=[sum(((s.detectors>>j)&1)<<i for i,s in enumerate(terminal))
          for j in range(len(circuit.detectors))]
    basis=nullspace(rows,len(terminal)); candidates=list(basis)
    for count,(a,b) in enumerate(combinations(basis,2)):
        if count>=pair_limit:break
        candidates.append(a^b)
    best=None
    for mask in sorted(set(candidates),key=lambda x:(x.bit_count(),x)):
        selected=[s for i,s in enumerate(terminal) if mask>>i&1]
        logical=0
        for s in selected:logical^=s.logical
        if not logical:continue
        w=witness(circuit,selected).to_dict()
        if not verify_witness(circuit.to_dict(),w)['verified']:raise ArithmeticError('Readout-coset witness failed replay')
        best=w;break
    return dict(witness=best,upper_bound=best['fault_count'] if best else None,
                tested_masks=len(set(candidates)),method='physical_readout_nullspace_basis_and_bounded_pairs',
                lower_bound_claim=False)
