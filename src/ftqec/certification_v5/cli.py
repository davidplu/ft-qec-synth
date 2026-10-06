"""Public V0.5 search endpoint and bounded higher-distance certification."""
import argparse,json
from pathlib import Path
from ..codes.stabilizer import StabilizerCode
from ..circuits.memory import MemoryConfig
from ..resource_synthesis.design import Design
from ..resource_synthesis.search import ResourceConfig,run_resource_search
from ..resource_synthesis.certification import SignatureCache
from ..resource_synthesis.circuits import build_design,validate_ideal
from .pipeline import finish
from .exact import certify
from .artifacts import verify


def main(argv=None):
    p=argparse.ArgumentParser(description='V0.5 Pareto promotion and compression; bounded exact certification')
    sub=p.add_subparsers(dest='command',required=True)
    for name in ('search','certify'):
        s=sub.add_parser(name);s.add_argument('input');s.add_argument('-o','--output',required=True)
        s.add_argument('--target-dc',type=int,default=3);s.add_argument('--rounds',type=int,default=3)
        s.add_argument('--basis',choices=('X','Z'),default='Z');s.add_argument('--logical-index',type=int,default=0)
        if name=='search':
            s.add_argument('--budget',type=int,default=48);s.add_argument('--seed',type=int,default=10)
            s.add_argument('--certification-work',type=int,default=20000000)
            s.add_argument('--descent-evaluations',type=int,default=256)
        else:
            s.add_argument('--design',required=True);s.add_argument('--work-limit',type=int,default=1048576)
            s.add_argument('--table-limit',type=int,default=250000)
    args=p.parse_args(argv);code=StabilizerCode.from_dict(json.loads(Path(args.input).read_text()))
    memory=MemoryConfig(args.rounds,args.basis,args.logical_index)
    if args.command=='search':
        cfg=ResourceConfig(budget=args.budget,seed=args.seed,target_dc=args.target_dc)
        native=run_resource_search(code,memory,cfg)
        out=finish(code,memory,native,args.target_dc,args.certification_work,args.descent_evaluations)
    else:
        design=Design.from_dict(json.loads(Path(args.design).read_text()));c=build_design(code,design,memory)
        ideal=validate_ideal(c)
        if not ideal['verified']:out=dict(region='INVALID_STRUCTURE',ideal_validation=ideal)
        else:
            ss,_=SignatureCache().get(c);bounds=certify(c,ss,args.target_dc,args.work_limit,args.table_limit)
            out=dict(bounds=bounds,independent_verification=verify(c,bounds),circuit=c.to_dict())
    path=Path(args.output);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(out,indent=2,allow_nan=False)+'\n',encoding='utf-8')


if __name__=='__main__':main()
