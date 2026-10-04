"""Seeded, profiled development benchmark; no held-out input."""
import argparse, cProfile, json, time
from pathlib import Path
from ftqec.codes.stabilizer import StabilizerCode
from ftqec.search.engine import search

def main():
    p=argparse.ArgumentParser(); p.add_argument('--budget',type=int,default=24); p.add_argument('--max-weight',type=int,default=2)
    args=p.parse_args(); root=Path(__file__).resolve().parents[1]; out=root/'results/development'; out.mkdir(parents=True,exist_ok=True)
    profiler=cProfile.Profile(); profiler.enable(); summary=[]
    for file in sorted((root/'benchmarks/development').glob('*.json')):
        code=StabilizerCode.from_dict(json.loads(file.read_text()))
        result=search(code,args.budget,seed=20261003,max_weight=args.max_weight,max_combinations=500000)
        (out/(file.stem+'.json')).write_text(json.dumps(result,indent=2)+'\n')
        summary.append(dict(code=code.name,candidates=result['candidates_evaluated'],rejections=result['rejections'],
                            stage_outcomes=result['stage_outcomes'],frontier_size=len(result['frontier']),runtime_seconds=result['runtime_seconds'],
                            best=[dict(id=r['architecture_id'],resources=r['resources'],bounds=r['bounds']) for r in result['frontier']]))
    profiler.disable(); profiler.dump_stats(str(out/'profile.pstats'))
    import pstats
    stats=pstats.Stats(profiler)
    rows=[dict(file=f,line=l,function=n,calls=v[1],self_seconds=v[2],cumulative_seconds=v[3]) for (f,l,n),v in stats.stats.items()]
    rows.sort(key=lambda r:r['cumulative_seconds'],reverse=True)
    (out/'profile.json').write_text(json.dumps(rows[:30],indent=2)+'\n')
    (out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps(summary,indent=2))

if __name__=='__main__': main()
