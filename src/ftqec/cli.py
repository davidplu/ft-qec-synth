import argparse, json
from pathlib import Path
from .codes.stabilizer import StabilizerCode
from .codes.logicals import logical_basis
from .architectures.generators import generate
from .circuits.extraction import build
from .circuits.model import Circuit
from .evaluation.resources import resources
from .evaluation.pareto import frontier
from .faults.signatures import signatures
from .faults.search import search_faults
from .search.engine import search

def main(argv=None):
    parser=argparse.ArgumentParser(description='Generic stabilizer architecture synthesis')
    sub=parser.add_subparsers(dest='command',required=True)
    for name in ('validate','generate','search','evaluate','faults','frontier'):
        p=sub.add_parser(name); p.add_argument('input'); p.add_argument('--output','-o')
        if name in ('generate','search'):
            p.add_argument('--seed',type=int,default=0); p.add_argument('--budget',type=int,default=100)
        if name=='search': p.add_argument('--required-distance',type=int,default=2)
        if name in ('search','faults'):
            p.add_argument('--max-weight',type=int,choices=(1,2,3),default=2)
            p.add_argument('--max-combinations',type=int,default=2000000); p.add_argument('--idles',action='store_true')
    args=parser.parse_args(argv)
    try:
        path=Path(args.input)
        if args.command=='frontier':
            groups={}
            for file in sorted(path.glob('*.json')) if path.is_dir() else [path]:
                d=json.loads(file.read_text())
                if isinstance(d,dict) and 'code_input_hash' in d and 'frontier' in d:
                    groups.setdefault(d['code_input_hash'],[]).extend(d['frontier'])
            if not groups: raise ValueError('No search-result JSON objects found')
            out={h:frontier(rs) for h,rs in groups.items()}
        else:
            d=json.loads(path.read_text())
            if args.command in ('validate','generate','search'):
                code=StabilizerCode.from_dict(d)
                if args.command=='validate': out=dict(**code.metrics(),logicals=[[str(a),str(b)] for a,b in logical_basis(code)])
                elif args.command=='generate': out=[dict(architecture_id=c.id,candidate=c.to_dict(),circuit=build(code,c).to_dict()) for c in generate(code,args.budget,args.seed)]
                else: out=search(code,args.budget,args.seed,args.max_weight,args.max_combinations,idles=args.idles,required_distance=args.required_distance)
            else:
                circuit=Circuit.from_dict(d)
                out=resources(circuit) if args.command=='evaluate' else search_faults(circuit,signatures(circuit,args.idles),args.max_weight,args.max_combinations)
        text=json.dumps(out,indent=2)
        if args.output:
            output=Path(args.output); output.parent.mkdir(parents=True,exist_ok=True); output.write_text(text+'\n')
        else: print(text)
    except (ValueError,KeyError,OSError) as exc: parser.error(str(exc))

if __name__=='__main__': main()
