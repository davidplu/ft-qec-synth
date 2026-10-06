"""Supplement missing unvisited-neighbor IDs without altering frozen raw runs."""
from pathlib import Path
from hashlib import sha256
import gzip,json
from ftqec.codes.stabilizer import StabilizerCode
from ftqec.circuits.memory import MemoryConfig
from ftqec.certification_v5.pending import inventory
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'results/v0.5'
result=[]
for p in sorted((OUT/'canonical_completion').glob('*.gz')):
    r=json.loads(gzip.decompress(p.read_bytes()));primary=json.loads(gzip.decompress((OUT/'raw'/p.name).read_bytes()))
    rows={x['architecture_id']:x for x in r['descent']['records']}
    for i in r['descent']['frontier']:
        audit=r['descent']['audits'][i]
        if audit['label']!='UNRESOLVED_MINIMALITY':continue
        pending=inventory(StabilizerCode.from_dict(primary['code']),MemoryConfig(**primary['memory_configuration']),rows[i])
        visited={x['child_id'] for x in audit['edits']}
        result.append(dict(run=p.name,id=i,canonical_raw_sha256=sha256(p.read_bytes()).hexdigest(),
            pending=[x for x in pending if x['child_id'] not in visited],evaluation_cap=1024,
            certification_work_limit=20000000,inventory_only=True,certification_performed=False))
(OUT/'pending_neighbor_inventory.json').write_text(json.dumps(result,indent=2)+'\n')
print('Finite pending inventories:',len(result),'neighbors:',sum(len(r['pending']) for r in result))
