"""Exact frozen-trace replay: recognition and descent are separate endpoints."""
from pathlib import Path
from hashlib import sha256
from dataclasses import asdict
import gzip,json,time,argparse,ctypes
from ftqec.codes.stabilizer import StabilizerCode
from ftqec.circuits.memory import MemoryConfig
from ftqec.resource_synthesis.design import Design
from ftqec.resource_synthesis.circuits import build_design
from ftqec.resource_synthesis.certification import SignatureCache
from ftqec.resource_synthesis.pareto import frontier,minima
from ftqec.certification_v5.staged import Budget,unknown_frontier,priority,escalate
from ftqec.certification_v5.descent import descend

ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'results/v0.5'


def dump(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    data=(json.dumps(value,indent=2,allow_nan=False)+'\n').encode()
    path.write_bytes(gzip.compress(data,mtime=0) if path.suffix=='.gz' else data)


def check_preservation():
    p=json.loads((OUT/'preservation.json').read_text())
    for name,h in p['hashes'].items():
        if sha256((ROOT/name).read_bytes()).hexdigest()!=h: raise AssertionError('Historical file changed: '+name)
    return len(p['hashes'])


def freeze():
    files=list((ROOT/'src/ftqec/certification_v5').glob('*.py'))+[Path(__file__).resolve(),ROOT/'docs/V0_5_PROTOCOL.md']
    payload=dict(baseline_commit='67a7f2948d5df1d1096489a123adff2501789be6',
                 hashes={p.relative_to(ROOT).as_posix():sha256(p.read_bytes()).hexdigest() for p in files},
                 search_budget=48,certification_work=20000000,descent_evaluations=256,seeds=[10,11,12])
    p=OUT/'experiment_snapshot.json'
    if p.exists():
        if json.loads(p.read_text())!=payload: raise AssertionError('Prospective experiment source changed')
    else: dump(p,payload)
    return sha256(p.read_bytes()).hexdigest()


def replay(path,shared):
    started=time.perf_counter(); old=json.loads(gzip.decompress(path.read_bytes()))
    code=StabilizerCode.from_dict(old['code']); memory=MemoryConfig(**old['memory_configuration'])
    unique={r['architecture_id']:r for r in old['records']}; rows=list(unique.values())
    native=frontier([r for r in rows if r['region']=='VALID']); budget=Budget();cache=SignatureCache()
    relevant=sorted(unknown_frontier(rows),key=lambda r:priority(r,rows,3))
    for rec in relevant:
        # Reassess after every promotion: dominated UNKNOWNs receive no extra work.
        if rec['architecture_id'] not in {r['architecture_id'] for r in unknown_frontier(rows)}:continue
        c=build_design(code,Design.from_dict(rec['design']),memory)
        promoted=escalate(rec,c,3,budget,cache)
        rows=[promoted if r['architecture_id']==rec['architecture_id'] else r for r in rows]
    promoted=frontier([r for r in rows if r['region']=='VALID']); promotion_work=budget.used
    descent=descend(code,memory,promoted,3,budget,shared=shared)
    unknown=unknown_frontier(rows+descent['records'])
    result=dict(schema_version='0.5',trace_path=path.relative_to(ROOT).as_posix(),
                trace_sha256=sha256(path.read_bytes()).hexdigest(),code=old['code'],memory_configuration=old['memory_configuration'],
                configuration=old['configuration'],initial_design_ids=old['initial_design_ids'],search_slots=old['evaluation_slots'],
                native_frontier=[r['architecture_id'] for r in native],native_minima=minima(native),
                promoted_frontier=[r['architecture_id'] for r in promoted],promoted_minima=minima(promoted),
                promotion_records=rows,descent=descent,unknown_pareto=[r['architecture_id'] for r in unknown],
                certification_budget=asdict(budget),promotion_work=promotion_work,
                runtime_seconds=time.perf_counter()-started)
    return result


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--task');args=ap.parse_args()
    preserved=check_preservation();snapshot=freeze(); shared={}
    paths=sorted((ROOT/'results/v0.4/raw').glob('primary*--v04--*.json.gz'))
    if args.task: paths=[p for p in paths if args.task in p.name]
    for path in paths:
        out=OUT/'raw'/path.name
        if out.exists():continue
        result=replay(path,shared);result['experiment_snapshot_sha256']=snapshot;dump(out,result)
        print(path.name,'native',len(result['native_frontier']),'promoted',len(result['promoted_frontier']),
              'final',len(result['descent']['frontier']),'evaluations',result['descent']['new_evaluations'],
              'seconds',round(result['runtime_seconds'],2),flush=True)
    dump(OUT/'preservation_verification.json',dict(verified=True,files=check_preservation()))


if __name__=='__main__':main()
