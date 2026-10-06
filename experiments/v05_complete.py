"""Resumable, separate final-audit completion for unchanged primary replay runs."""
from pathlib import Path
from hashlib import sha256
import gzip,json
from ftqec.codes.stabilizer import StabilizerCode
from ftqec.circuits.memory import MemoryConfig
from ftqec.certification_v5.completion import complete

OUT=Path(__file__).resolve().parents[1]/'results/v0.5';(OUT/'completion').mkdir(exist_ok=True)
for p in sorted((OUT/'raw').glob('*.json.gz')):
    dest=OUT/'completion'/p.name
    if dest.exists():continue
    r=json.loads(gzip.decompress(p.read_bytes()));code=StabilizerCode.from_dict(r['code']);memory=MemoryConfig(**r['memory_configuration'])
    result=complete(code,memory,r['descent']['records'],r['descent']['frontier'],3,r['certification_budget']['used'])
    result.update(primary_run=p.name,primary_sha256=sha256(p.read_bytes()).hexdigest())
    dest.write_bytes(gzip.compress(json.dumps(result,indent=2).encode(),mtime=0))
    d=result['descent'];print(p.name,'new',d['new_evaluations'],'final',len(d['frontier']),
        [d['audits'][i]['label'] for i in d['frontier']],'seconds',round(d['runtime_seconds'],2),flush=True)
