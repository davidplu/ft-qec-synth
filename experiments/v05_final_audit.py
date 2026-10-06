"""Fresh physical verification of all final endpoints and all projection proofs."""
from pathlib import Path
from hashlib import sha256
import gzip,json,time
from ftqec.codes.stabilizer import StabilizerCode
from ftqec.circuits.memory import MemoryConfig
from ftqec.circuits.model import Circuit
from ftqec.resource_synthesis.design import Design
from ftqec.resource_synthesis.circuits import build_design,validate_ideal
from ftqec.resource_synthesis.certification import fingerprint
from ftqec.evaluation.resources import resources
from ftqec.faults.verification import verify_witness,replay
from ftqec.certification_v5.low_audit import exclude
from ftqec.certification_v5.projection import verify
import v05_replay as original

ROOT=original.ROOT;OUT=original.OUT
def read(p):return json.loads(gzip.decompress(p.read_bytes()))
def witness(c,w):
    if w:
        assert w['fault_count']==len(w['faults'])
        assert verify_witness(c.to_dict(),w)['verified']
def main():
    started=time.perf_counter();preserved=original.check_preservation()
    snapshot=OUT/'experiment_snapshot.json'
    for name,h in json.loads(snapshot.read_text())['hashes'].items():assert sha256((ROOT/name).read_bytes()).hexdigest()==h,name
    finals=[]
    for path in sorted((OUT/'raw').glob('*.gz')):
        r=read(path);old=ROOT/r['trace_path'];oldrow=read(old)
        assert sha256(old.read_bytes()).hexdigest()==r['trace_sha256']
        assert r['initial_design_ids']==oldrow['initial_design_ids'] and r['search_slots']==48
        assert r['configuration']==oldrow['configuration'] and r['code']==oldrow['code']
        assert r['experiment_snapshot_sha256']==sha256(snapshot.read_bytes()).hexdigest()
        code=StabilizerCode.from_dict(r['code']);memory=MemoryConfig(**r['memory_configuration'])
        for phase in ('raw','completion','canonical_completion'):
            data=read(OUT/phase/path.name);d=data['descent'];rows={x['architecture_id']:x for x in d['records']}
            if phase!='raw':assert data['primary_sha256']==sha256(path.read_bytes()).hexdigest()
            if phase=='canonical_completion':assert data['completion_sha256']==sha256((OUT/'completion'/path.name).read_bytes()).hexdigest()
            for i in d['frontier']:
                row=rows[i];c=build_design(code,Design.from_dict(row['design']),memory)
                assert fingerprint(c)==row['circuit_hash'] and resources(c)==row['resources']
                assert validate_ideal(c)['verified'] and row['bounds']['lower_bound']>=3
                assert exclude(c,2)['verified'];witness(c,row['bounds'].get('witness'))
                finals.append(dict(run=path.name,phase=phase,id=i,verified=True))
    proofs=[]
    for path in sorted((OUT/'projection_ladder').glob('*.gz')):
        r=read(path);c=Circuit.from_dict(r['circuit']);check=verify(c,r['certificate'])
        assert check['verified'];witness(c,r['upper']['witness'])
        assert r['upper']['upper_bound']==len(r['upper']['witness']['faults'])
        proofs.append(dict(name=r['name'],lower=r['certificate']['lower_bound'],upper=r['upper']['upper_bound'],verified=True))
    negative=[]
    for phase in ('sat_ladder','prefix_ladder'):
        for path in (OUT/phase).glob('*.gz'):
            r=read(path);c=Circuit.from_dict(r['circuit'])
            # Recursively inspect every explicit witness, including independent joins.
            def walk(v):
                if isinstance(v,dict):
                    if 'violating_faults' in v:
                        actual=replay(c.to_dict(),v['violating_faults'])
                        assert not actual['detector_outcomes'] and actual['logical_coset']
                        negative.append(path.name)
                    if 'fault_count' in v and 'faults' in v:witness(c,v);negative.append(path.name)
                    else:
                        for child in v.values():walk(child)
                elif isinstance(v,list):
                    for child in v:walk(child)
            walk(r)
    result=dict(verified=True,historical_files=preserved,finalists=finals,projection_proofs=proofs,
                higher_witness_checks=len(negative),runtime_seconds=time.perf_counter()-started)
    (OUT/'final_physical_verification.json').write_text(json.dumps(result,indent=2)+'\n')
    print('Verified historical',preserved,'final endpoints',len(finals),'projection proofs',len(proofs),flush=True)

if __name__=='__main__':main()
