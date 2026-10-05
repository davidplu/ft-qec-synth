"""Check saved experiment completeness, matched starts and persisted witnesses."""
from pathlib import Path
from collections import Counter
from dataclasses import asdict
import gzip,json,hashlib,time
import jsonschema
from v04_development import ROOT,OUT,SEEDS,assert_frozen,historical_check,dump
from ftqec.codes.stabilizer import StabilizerCode
from ftqec.architectures.candidate import Candidate
from ftqec.circuits.memory import MemoryConfig,build_memory
from ftqec.resource_synthesis.design import Design
from ftqec.resource_synthesis.circuits import build_design,validate_ideal
from ftqec.resource_synthesis.certification import classify,fingerprint
from ftqec.resource_synthesis.pareto import frontier,minima
from ftqec.faults.verification import verify_witness

def main():
    start=time.perf_counter(); freeze=assert_frozen(); starts={}; counts=Counter(); witness_count=0; unique={}; audits=0
    schema=json.loads((ROOT/'docs/schemas/result-v0.4.schema.json').read_text()); paths=sorted((OUT/'raw').glob('*.gz'))
    assert len(paths)==144, f'Expected 144 runs, found {len(paths)}'
    for path in paths:
        with gzip.open(path,'rt') as f: result=json.load(f)
        group,task,variant,seed=path.name[:-8].split('--'); counts[group]+=1
        assert result['software_git_commit']==freeze['algorithm_commit']
        assert result['evaluation_slots']==48 and len(result['records'])==48
        assert result['experiment_freeze_sha256']==hashlib.sha256((OUT/'experiment_freeze.json').read_bytes()).hexdigest()
        key=group,task,seed
        ids=result['initial_population_ids']
        if key in starts: assert starts[key]==ids,(key,'different initial population')
        starts[key]=ids
        code=StabilizerCode.from_dict(result['code']); memory=MemoryConfig(**result['memory_configuration'])
        if result['schema_version']=='0.4': jsonschema.validate(result,schema)
        for r in result['records']:
            idkey=code.input_hash,json.dumps(asdict(memory),sort_keys=True),r['architecture_id'],result['schema_version']
            if idkey not in unique:
                c=build_design(code,Design.from_dict(r['design']),memory) if result['schema_version']=='0.4' else build_memory(code,Candidate.from_dict(r['candidate']),memory)
                if result['schema_version']=='0.4':
                    assert fingerprint(c)==r['circuit_hash']
                    assert validate_ideal(c)==r['ideal_validation']
                    if r['region']!='INVALID_STRUCTURE': assert classify(r['bounds'],3)==r['region']
                witness=r['bounds'].get('witness')
                if witness:
                    assert verify_witness(c.to_dict(),witness)['verified'],path.name
                    witness_count+=1
                unique[idkey]=True
        valid=[r for r in result['records'] if r['bounds']['lower_bound']>=3 and r.get('region')!='INVALID_STRUCTURE']
        f=frontier(valid); summary=result.get('resource_summary',result['summary'])
        assert summary['minima_at_target']==minima(f)
        fids=result.get('resource_frontier',result.get('frontier',[]))
        assert set(fids)=={r['architecture_id'] for r in f}
        auditids={a['architecture_id'] for a in result['independent_final_audits'] if a['verified'] and a['excluded_through']==2}
        assert set(fids)<=auditids; audits+=len(auditids)
        if result['schema_version']=='0.4':
            assert (OUT/'minimality'/path.name).exists(),('missing minimality',path.name)
    assert dict(counts)=={'bare':18,'overprotected':12,'prefixprotected':6,'primary':108}
    v01=json.loads((OUT/'v01_preservation.json').read_text())
    for name,h in v01['hashes'].items():
        assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==h,name
    dump(OUT/'verification.json',{'verified':True,'run_count':len(paths),'groups':dict(counts),'evaluation_slots':48*len(paths),
        'matched_initial_population_blocks':len(starts),'unique_architectures_rebuilt':len(unique),
        'persisted_witnesses_independently_replayed':witness_count,'independent_frontier_certificates':audits,
        'historical_files_unchanged':historical_check()+len(v01['hashes']),'runtime_seconds':time.perf_counter()-start})
    print('verified',len(paths),'runs;',len(unique),'architectures;',witness_count,'witnesses;',audits,'final certificates',flush=True)

if __name__=='__main__': main()
