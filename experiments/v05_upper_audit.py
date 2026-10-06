"""Post-benchmark upper-witness supplement; does not change comparison search."""
from pathlib import Path
import gzip,json
from ftqec.circuits.model import Circuit
from ftqec.resource_synthesis.certification import SignatureCache
from ftqec.certification_v5.upper import terminal_witness

out=Path(__file__).resolve().parents[1]/'results/v0.5'
rows=json.loads(gzip.decompress((out/'ladder.json.gz').read_bytes()));result=[]
for row in rows:
    c=Circuit.from_dict(row['circuit']);ss,_=SignatureCache().get(c);u=terminal_witness(c,ss)
    result.append(dict(name=row['name'],lower_bound=row['bounds']['lower_bound'],**u))
    print(row['name'],row['bounds']['lower_bound'],u['upper_bound'])
(out/'upper_witnesses.json').write_text(json.dumps(result,indent=2)+'\n')
