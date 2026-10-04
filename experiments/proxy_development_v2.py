"""Unrelated generic size proxies; never imports any held-out code."""
from dataclasses import replace
import argparse,gzip,json
from development_v2 import OUT,BENCH,dump,assert_frozen,shor,pauli
from compare_development_v2 import rss
from ftqec.codes.stabilizer import StabilizerCode
from ftqec.search.malignant import MalignantConfig,run_malignant_search
from ftqec.circuits.memory import MemoryConfig,build_memory
from ftqec.architectures.candidate import Candidate
from ftqec.faults.exclusion import verify_exclusion
from ftqec.faults.verification import verify_witness

def main(n):
    assert_frozen();r,c,extra={23:(4,5,3),25:(5,5,0),31:(5,6,1),44:(6,7,2)}[n]
    gs=[g+'I'*extra for g in shor(r,c)]+[pauli(n,{r*c+i},'Z') for i in range(extra)]
    code=StabilizerCode.from_dict({'name':f'generic-shor-{r}x{c}-plus-{extra}-fixed-qubits-proxy','generators':gs})
    dump(BENCH/'proxies'/f'n{n}.json',{**code.to_dict(),'provenance':{'construction':'rectangular Shor tensor independent +Z stabilizer states',
         'distance':min(r,c),'held_out_information_used':False,'purpose':'runtime scaling only'}})
    result=run_malignant_search(code,MemoryConfig(3,'Z'),replace(MalignantConfig(),budget=32,seed=100))
    memory=rss();best=max(result['records'],key=lambda r:r['bounds']['lower_bound'])
    circuit=build_memory(code,Candidate.from_dict(best['candidate']),MemoryConfig(3,'Z'))
    cert=verify_exclusion(circuit,best['bounds']['lower_bound']-1);assert cert['verified']
    if best['bounds'].get('witness'):assert verify_witness(circuit,best['bounds']['witness'])['verified']
    path=OUT/'proxy_raw'/f'n{n}.json.gz';path.parent.mkdir(exist_ok=True)
    with gzip.open(path,'wt',encoding='utf-8') as f:json.dump(result,f,separators=(',',':'))
    unique=[r for r in result['records'] if not r['cached_evaluation']]
    summary={'name':code.name,'n':n,'check_count':len(gs),'rounds':3,'max_fault_weight':3,'evaluation_slots':32,
        'seconds':result['runtime_seconds'],'memory':memory,'best_dc':best['bounds']['lower_bound'],
        'independent_best_exclusion':cert,'certification_seconds':sum(r['fault_search_seconds'] for r in unique),
        'combinations_examined':sum(r['bounds']['combinations_examined'] for r in unique),
        'unique_architectures':len(unique),'distance_code':min(r,c),'held_out_runs':0,
        'boundary_upper_bound':'not used for runtime selection','spectrum_seconds':sum(r['spectrum_seconds'] for r in unique)}
    dump(OUT/'proxy_summaries'/f'n{n}.json',summary);print(json.dumps(summary),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('n',type=int,choices=(23,25,31,44));a=p.parse_args();main(a.n)
