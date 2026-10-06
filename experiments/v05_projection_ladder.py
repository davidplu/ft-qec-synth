"""Prospective selected-observable projection certificates on all predefined cases."""
from pathlib import Path
import gzip,json
from v05_ladder import shor,peak_memory
from ftqec.architectures.generators import generate
from ftqec.resource_synthesis.design import Design
from ftqec.resource_synthesis.circuits import build_design,validate_ideal
from ftqec.resource_synthesis.certification import SignatureCache
from ftqec.circuits.memory import MemoryConfig
from ftqec.certification_v5.projection import certify,verify
from ftqec.certification_v5.upper import terminal_witness

OUT=Path(__file__).resolve().parents[1]/'results/v0.5/projection_ladder';OUT.mkdir(parents=True,exist_ok=True)
for size in (5,7):
    for rounds in (1,3):
        for family in ('interval_flag','verified_cat'):
            for axis in ('X','Z'):
                name=f'shor-{size}x{size}-R{rounds}-{family}-{axis}';path=OUT/(name+'.json.gz')
                if path.exists():continue
                code=shor(size);d=Design(next(iter(generate(code,1,10))),family=family)
                c=build_design(code,d,MemoryConfig(rounds=rounds,basis=axis));ideal=validate_ideal(c)
                if not ideal['verified']:raise ArithmeticError('Invalid projection ladder circuit')
                cert=certify(c);independent=verify(c,cert);ss,_=SignatureCache().get(c);upper=terminal_witness(c,ss)
                if not independent['verified']:raise ArithmeticError('Projection certificate failed independent physical check')
                rec=dict(name=name,permanent_development=True,code=code.to_dict(),design=d.to_dict(),
                    circuit=c.to_dict(),target=size,ideal=ideal,certificate=cert,independent=independent,upper=upper,
                    exact=cert['lower_bound']==upper['upper_bound'],process_peak_working_set_bytes=peak_memory())
                path.write_bytes(gzip.compress(json.dumps(rec,indent=2).encode(),mtime=0))
                print(name,'lower',cert['lower_bound'],'upper',upper['upper_bound'],'independent',independent['verified'],
                      'coords',cert['coordinate_count'],'fault norm',cert['maximum_single_fault_coordinate_weight'],flush=True)
