"""Constraint-equivalent necessity audits with exact cross-run certificate caching."""
from pathlib import Path
from dataclasses import asdict
from collections import Counter
import gzip,json,time
from v04_development import ROOT,OUT,assert_frozen,dump
from ftqec.codes.stabilizer import StabilizerCode
from ftqec.circuits.memory import MemoryConfig
from ftqec.resource_synthesis.design import Design
from ftqec.resource_synthesis.search import ResourceConfig
from ftqec.resource_synthesis.audits import protection_audit

def main():
    assert_frozen(); cache={}; start=time.perf_counter(); counts=Counter()
    # Preload completed certificates from earlier identical audits; do not modify them.
    for p in sorted((OUT/'raw').glob('*.gz')):
        with gzip.open(p,'rt') as f: result=json.load(f)
        if result['schema_version']!='0.4': continue
        code=StabilizerCode.from_dict(result['code']); memory=MemoryConfig(**result['memory_configuration'])
        cfg=ResourceConfig(**result['configuration']); target=cfg.target_dc
        records={r['architecture_id']:r for r in result['records']}; fids=result['frontier']
        path=OUT/'minimality'/p.name
        if path.exists():
            with gzip.open(path,'rt') as f: old=json.load(f)
            from ftqec.resource_synthesis.audits import strict_minimality
            rows=[strict_minimality(a,records[a['parent']]['resources']) for a in old['audits']]
            for a in rows:
                key=(code.input_hash,json.dumps(asdict(memory),sort_keys=True),a['parent'],target,cfg.max_combinations)
                cache[key]=a
            counts['retained_existing']+=len(rows); continue
        rows=[]
        for fid in dict.fromkeys(fids):
            key=(code.input_hash,json.dumps(asdict(memory),sort_keys=True),fid,target,cfg.max_combinations)
            cached=key in cache
            if not cached: cache[key]=protection_audit(code,Design.from_dict(records[fid]['design']),memory,cfg)
            rows.append({**cache[key],'cached_certificate':cached}); counts['cached' if cached else 'new']+=1
        path.parent.mkdir(parents=True,exist_ok=True)
        temp=path.with_suffix(path.suffix+'.tmp')
        with gzip.open(temp,'wt') as f: json.dump({'run':p.name,'audits':rows},f,allow_nan=False)
        temp.replace(path)
        print('constraint_minimality',p.name,len(rows),flush=True)
    dump(OUT/'minimality_timing.json',{'counts':dict(counts),'seconds':time.perf_counter()-start,
         'optimization':'omit unused diagnostic spectrum; identical physical design/memory/target/cap certificate reuse; final exclusion unchanged'})

if __name__=='__main__': main()
