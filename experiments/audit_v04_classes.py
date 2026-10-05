"""Whole-class repair diagnostics using independent physical singleton replay."""
from collections import defaultdict
from hashlib import sha256
from pathlib import Path
import gzip,json
from v04_development import ROOT,OUT,assert_frozen,dump
from ftqec.codes.stabilizer import StabilizerCode
from ftqec.circuits.memory import MemoryConfig
from ftqec.resource_synthesis.design import Design
from ftqec.resource_synthesis.circuits import build_design
from ftqec.resource_synthesis.certification import SignatureCache,METRICS
from ftqec.resource_synthesis.audits import class_eliminated,strict_minimality
from ftqec.faults.spectrum import malignant_spectrum,representative_witness,classify
from ftqec.faults.signatures import enumerate_faults
from ftqec.faults.batch_verification import singleton_effects
from ftqec.faults.analysis import semantic_address

def main():
    assert_frozen(); runs=[]; statistics=defaultdict(lambda:dict(attempts=0,eliminated=0,survived=0,unknown=0))
    for p in sorted((OUT/'raw').glob('*.gz')):
        with gzip.open(p,'rt') as f: result=json.load(f)
        if result['schema_version']!='0.4': continue
        code=StabilizerCode.from_dict(result['code']); memory=MemoryConfig(**result['memory_configuration'])
        bynode={r['evaluation_index']:r for r in result['records']}; circuits={}; cache=SignatureCache(); parent_data={}
        def circuit(record):
            key=record['architecture_id']
            if key not in circuits: circuits[key]=build_design(code,Design.from_dict(record['design']),memory)
            return circuits[key]
        outcomes=[]
        for child in result['records']:
            provenance=child['provenance']; source_id=provenance.get('source_counterexample_id')
            if not source_id: continue
            parent=bynode[provenance['parent_evaluation']]; pc=circuit(parent); cc=circuit(child)
            if parent['architecture_id'] not in parent_data:
                ss,_=cache.get(pc); spec,members=malignant_spectrum(pc,ss,2,result['configuration']['max_combinations'])
                targets={}
                for cls in spec['classes']:
                    witness=representative_witness(pc,ss,cls)
                    identifier=sha256(json.dumps(witness,sort_keys=True).encode()).hexdigest()[:20]
                    targets[identifier]=cls
                if parent['bounds'].get('witness'):
                    witness=parent['bounds']['witness']; index={(s.fault.location,s.fault.label):s for s in ss}
                    group=[index[(f['location'],f['label'])] for f in witness['faults']]
                    cid=classify(pc,group).id; cls=next((c for c in spec['classes'] if c['id']==cid),None)
                    if cls: targets[sha256(json.dumps(witness,sort_keys=True).encode()).hexdigest()[:20]]=cls
                parent_data[parent['architecture_id']]=(ss,spec,members,targets)
            ss,spec,members,targets=parent_data[parent['architecture_id']]; target=targets.get(source_id)
            eliminated=None; count=None; complete=False
            if target and child['ideal_validation']['verified']:
                complete=spec['layers'][str(target['weight'])]['complete']
                faults=list(enumerate_faults(cc)); effects=singleton_effects(cc,faults)
                lookup={(f.operation,f.label):effects[i] for i,f in enumerate(faults)}
                addresses=defaultdict(list)
                for i in range(len(cc.operations)): addresses[semantic_address(cc,i)].append(i)
                mappings={}
                for indices in members[target['id']]:
                    for index in indices:
                        if index in mappings: continue
                        fault=ss[index].fault; positions=addresses.get(semantic_address(pc,fault.operation),[])
                        if len(positions)!=1: mappings[index]=None; continue
                        pos=positions[0]; value=lookup.get((pos,fault.label))
                        mappings[index]=None if value is None else (f'op:{pos}',*value)
                count=len(members[target['id']]); eliminated=class_eliminated(members[target['id']],mappings)
                if not complete and eliminated is True: eliminated=None
            row={'run':p.name,'evaluation':child['evaluation_index'],'operator':provenance['operator'],
                'source_class_id':target['id'] if target else None,'observed_realizations':count,
                'source_layer_complete':complete,'whole_class_eliminated':eliminated,
                'delta':{m:child['resources'][m]-parent['resources'][m] for m in METRICS}}
            outcomes.append(row); stat=statistics[row['operator']]; stat['attempts']+=1
            stat['eliminated' if eliminated is True else 'survived' if eliminated is False else 'unknown']+=1
        runs.extend(outcomes)
        # Strict local minimality is a reporting refinement, no search changes.
        auditpath=OUT/'minimality'/p.name
        if auditpath.exists():
            with gzip.open(auditpath,'rt') as f: audits=json.load(f)
            records={r['architecture_id']:r for r in result['records']}
            audits['audits']=[strict_minimality(a,records[a['parent']]['resources']) for a in audits['audits']]
            with gzip.open(auditpath,'wt') as f: json.dump(audits,f,allow_nan=False)
        print('class_audit',p.name,len(outcomes),flush=True)
    dump(OUT/'whole_class_repair_audit.json',{'statistics':{op:{**s,
        'probability_eliminates_complete_transportable_class':s['eliminated']/(s['eliminated']+s['survived'])
           if s['eliminated']+s['survived'] else None} for op,s in statistics.items()},'outcomes':runs,
        'method':'parent native complete class enumeration; independent child physical singleton replay; all class realizations',
        'unknown_policy':'partial source layers, removed or ambiguous locations receive no elimination credit'})

if __name__=='__main__': main()
