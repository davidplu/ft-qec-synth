"""Prospective permanent-development physical-variant SAT supplement."""
from pathlib import Path
import gzip,json,time
from v05_ladder import shor,peak_memory
from ftqec.architectures.generators import generate
from ftqec.circuits.memory import MemoryConfig
from ftqec.resource_synthesis.design import Design
from ftqec.resource_synthesis.circuits import build_design,validate_ideal
from ftqec.resource_synthesis.certification import SignatureCache
from ftqec.certification_v5.exact import certify
from ftqec.certification_v5.upper import terminal_witness
from ftqec.certification_v5.sat_audit import exclusion

OUT=Path(__file__).resolve().parents[1]/'results/v0.5/sat_ladder';OUT.mkdir(parents=True,exist_ok=True)
for size in (4,5,7):
    for rounds in (1,3):
        path=OUT/f'shor-{size}x{size}-R{rounds}.json.gz'
        if path.exists():continue
        code=shor(size);d=Design(next(iter(generate(code,1,10))),family='verified_cat')
        c=build_design(code,d,MemoryConfig(rounds=rounds,basis='Z'));ideal=validate_ideal(c)
        if not ideal['verified']:raise ArithmeticError('Invalid ladder circuit')
        ss,_=SignatureCache().get(c);native=certify(c,ss,size,1048576,250000);upper=terminal_witness(c,ss)
        model=OUT/f'shor-{size}x{size}-R{rounds}-exclude.bin'
        checked=exclusion(c,size-1,model_path=model)
        threshold=exclusion(c,size) if size>=5 else None
        rec=dict(name=f'shor-{size}x{size}-R{rounds}',permanent_development=True,code=code.to_dict(),
            design=d.to_dict(),circuit=c.to_dict(),target=size,native=native,upper=upper,independent=checked,
            threshold_check=threshold,process_peak_working_set_bytes=peak_memory(),model_path=model.name)
        path.write_bytes(gzip.compress(json.dumps(rec,indent=2).encode(),mtime=0))
        print(rec['name'],'native LB',native['lower_bound'],'SAT',checked['status'],'UB',upper['upper_bound'],
            'time',round(checked['runtime_seconds'],2),flush=True)
