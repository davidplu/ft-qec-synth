"""Prospective generic existing-family prefix development certification ladder."""
from pathlib import Path
from dataclasses import replace
import gzip,json
from v05_ladder import shor,peak_memory
from ftqec.architectures.generators import generate
from ftqec.resource_synthesis.design import Design
from ftqec.resource_synthesis.circuits import build_design,validate_ideal
from ftqec.resource_synthesis.certification import SignatureCache
from ftqec.circuits.memory import MemoryConfig
from ftqec.certification_v5.exact import certify
from ftqec.certification_v5.upper import terminal_witness
from ftqec.certification_v5.pair_audit import exclusion as pair_exclusion
from ftqec.certification_v5.sat_audit import exclusion as sat_exclusion

OUT=Path(__file__).resolve().parents[1]/'results/v0.5/prefix_ladder';OUT.mkdir(parents=True,exist_ok=True)
for size in (5,7):
    for rounds in (1,3):
        path=OUT/f'shor-{size}x{size}-R{rounds}.json.gz'
        if path.exists():continue
        code=shor(size);a=next(iter(generate(code,1,10)))
        a=replace(a,flag_intervals=tuple(tuple((0,p) for p in range(1,len(o)+1)) for o in a.orders))
        design=Design(a,shared_flags=True);c=build_design(code,design,MemoryConfig(rounds=rounds,basis='Z'))
        if not validate_ideal(c)['verified']:raise ArithmeticError('Invalid prefix ladder circuit')
        ss,_=SignatureCache().get(c);native=certify(c,ss,size,4000000,500000);upper=terminal_witness(c,ss)
        independent=pair_exclusion(c,min(4,size-1),16000000,500000)
        sat=sat_exclusion(c,size-1,model_path=OUT/f'shor-{size}x{size}-R{rounds}.bin')
        r=dict(name=f'shor-{size}x{size}-R{rounds}',permanent_development=True,code=code.to_dict(),
            design=design.to_dict(),circuit=c.to_dict(),target=size,native=native,upper=upper,
            independent_pair=independent,sat=sat,process_peak_working_set_bytes=peak_memory())
        path.write_bytes(gzip.compress(json.dumps(r,indent=2).encode(),mtime=0))
        print(r['name'],'native',native['lower_bound'],native['upper_bound'],'independent',independent['verified'],
            independent['excluded_through'],'SAT',sat['status'],flush=True)
