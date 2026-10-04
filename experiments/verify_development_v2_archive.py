"""Verify saved comparison hashes, inputs, parameters and matched populations."""
from collections import Counter
from dataclasses import asdict, replace
import gzip
import json

from compare_development_v2 import ROOT, OUT, VARIANTS, check_protocol, sha, dump
from ftqec.architectures.candidate import Candidate
from ftqec.codes.stabilizer import StabilizerCode
from ftqec.circuits.memory import MemoryConfig
from ftqec.search.malignant import MalignantConfig


def main():
    m=check_protocol();tasks={t['task']:t for t in m['tasks']}
    files=json.loads((OUT/'raw_manifest.json').read_text())
    expected={(t,s,v) for t in tasks for s in m['final_seeds']
              for v in m['primary_variants']+m['secondary_ablations']
              if v in m['primary_variants'] or s in m['secondary_ablation_seeds']}
    actual=set();populations={};commits=set();slots=0;counts=Counter()
    for entry in files:
        path=ROOT/entry['file']
        assert path.stat().st_size==entry['bytes'] and sha(path)==entry['sha256']
        with gzip.open(path,'rt',encoding='utf-8') as f:r=json.load(f)
        t=tasks[r['development_task']];s=r['configuration']['seed'];v=r['experiment_variant']
        key=(t['task'],s,v);assert key in expected and key not in actual;actual.add(key)
        assert r['frozen_algorithm_commit']==m['algorithm_commit']
        assert r['benchmark_manifest_sha256']==sha(ROOT/'benchmarks/development_v2/MANIFEST.json')
        config=replace(MalignantConfig(),budget=m['evaluation_budget'],seed=s,target_dc=t['d_target'],
                       strategy=v if v in m['primary_variants'] else 'v03',**VARIANTS[v])
        assert r['configuration']==asdict(config)
        assert r['memory_configuration']==asdict(MemoryConfig(3,t['basis']))
        code=StabilizerCode.from_dict(json.loads((ROOT/t['code_path']).read_text()))
        assert r['code']==code.to_dict()
        assert r['evaluation_slots']==m['evaluation_budget']==len(r['records'])
        ids=r['initial_population_ids'];assert len(ids)==config.initial_population
        assert ids==[Candidate.from_dict(x['candidate']).id for x in r['records'][:len(ids)]]
        popkey=(t['task'],s)
        if popkey in populations:assert populations[popkey]==ids
        populations[popkey]=ids
        commits.add(r['software_git_commit']);slots+=r['evaluation_slots'];counts[v]+=1
    assert actual==expected and len(commits)==1
    check_protocol()
    summary={'verified':True,'runs':len(actual),'evaluation_slots':slots,
             'matched_task_seed_populations':len(populations),'variants':dict(counts),
             'recorded_experiment_commits':sorted(commits),'frozen_algorithm_commit':m['algorithm_commit'],
             'raw_hashes_verified':len(files),'algorithm_and_previous_results_unchanged':True}
    dump(OUT/'archive_verification.json',summary)
    print(json.dumps(summary,indent=2))


if __name__=='__main__':main()
