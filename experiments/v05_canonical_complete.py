"""Separate canonical-ID, exact-physical-cache closure supplement."""
from pathlib import Path
from hashlib import sha256
import gzip,json
from ftqec.codes.stabilizer import StabilizerCode
from ftqec.circuits.memory import MemoryConfig
from ftqec.certification_v5.canonical import complete

OUT=Path(__file__).resolve().parents[1]/'results/v0.5';(OUT/'canonical_completion').mkdir(exist_ok=True)
for path in sorted((OUT/'raw').glob('*.json.gz')):
    prior=OUT/'completion'/path.name;dest=OUT/'canonical_completion'/path.name
    if not prior.exists() or dest.exists():continue
    r=json.loads(gzip.decompress(path.read_bytes()));p=json.loads(gzip.decompress(prior.read_bytes()))
    rows={x['architecture_id']:x for x in r['descent']['records']}
    rows.update({x['architecture_id']:x for x in p['descent']['records']})
    code=StabilizerCode.from_dict(r['code']);memory=MemoryConfig(**r['memory_configuration'])
    result=complete(code,memory,list(rows.values()),p['descent']['frontier'],3,p['combined_used_work'])
    result.update(primary_run=path.name,primary_sha256=sha256(path.read_bytes()).hexdigest(),
                  completion_sha256=sha256(prior.read_bytes()).hexdigest())
    dest.write_bytes(gzip.compress(json.dumps(result,indent=2).encode(),mtime=0))
    d=result['descent'];print(path.name,'new',d['new_evaluations'],'cache hits',result['physical_certificate_cache_hits'],
        'labels',[d['audits'][i]['label'] for i in d['frontier']],'seconds',round(d['runtime_seconds'],2),flush=True)
