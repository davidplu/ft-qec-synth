"""V0.4 CLI; historical commands remain accessible through ftqec-v03."""
import argparse, json
from pathlib import Path
from ..codes.stabilizer import StabilizerCode
from ..circuits.memory import MemoryConfig
from .search import ResourceConfig, run_resource_search, protection_audit
from .design import Design
from .pareto import METRICS, tiers


def main(argv=None):
    p=argparse.ArgumentParser(description='Resource Pareto synthesis subject to certified circuit distance')
    sub=p.add_subparsers(dest='command',required=True)
    s=sub.add_parser('search'); s.add_argument('input'); s.add_argument('-o','--output',required=True)
    s.add_argument('--target-dc',type=int,default=3); s.add_argument('--budget',type=int,default=48)
    s.add_argument('--seed',type=int,default=10); s.add_argument('--rounds',type=int,default=3)
    s.add_argument('--basis',choices=('X','Z'),default='Z'); s.add_argument('--logical-index',type=int,default=0)
    s.add_argument('--max-combinations',type=int,default=200000)
    s.add_argument('--no-basis-search',action='store_true'); s.add_argument('--no-new-family',action='store_true')
    s.add_argument('--strategy',choices=('repair_compress','repair_only'),default='repair_compress')
    s.add_argument('--select',choices=('QD','Q')); s.add_argument('--depth-limit',type=int)
    s.add_argument('--minimality',action='store_true')
    f=sub.add_parser('frontier'); f.add_argument('input'); f.add_argument('--target-dc',type=int,default=3)
    f.add_argument('-o','--output')
    args=p.parse_args(argv)
    if args.command=='search':
        code=StabilizerCode.from_dict(json.loads(Path(args.input).read_text()))
        cfg=ResourceConfig(budget=args.budget,seed=args.seed,target_dc=args.target_dc,
            max_combinations=args.max_combinations,strategy=args.strategy,
            basis_search=not args.no_basis_search,new_family=not args.no_new_family)
        memory=MemoryConfig(args.rounds,args.basis,args.logical_index)
        out=run_resource_search(code,memory,cfg)
        valid=[r for r in out['records'] if r['architecture_id'] in out['frontier']]
        if args.depth_limit is not None: valid=[r for r in valid if r['resources']['D']<=args.depth_limit]
        if args.select: out['user_selected_architecture']=min(valid,key=lambda r:r['resources'][args.select])['architecture_id'] if valid else None
        if args.minimality:
            out['local_minimality']=[protection_audit(code,Design.from_dict(r['design']),memory,cfg) for r in valid]
    else:
        result=json.loads(Path(args.input).read_text()); out=tiers(result['records']).get(str(args.target_dc),{'architecture_ids':[],'minima':{m:None for m in METRICS}})
    text=json.dumps(out,indent=2,allow_nan=False)+'\n'
    if args.output:
        path=Path(args.output); path.parent.mkdir(parents=True,exist_ok=True); path.write_text(text)
    else: print(text)


if __name__=='__main__': main()
