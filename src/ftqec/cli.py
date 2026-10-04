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
    for name in ('validate','generate','memory','search','evaluate','faults','frontier','decode','verify','spectrum'):
        p=sub.add_parser(name); p.add_argument('input'); p.add_argument('--output','-o')
        if name in ('generate','search'):
            p.add_argument('--seed',type=int,default=0); p.add_argument('--budget',type=int,default=100)
        if name=='search':
            p.add_argument('--required-distance', '--target-dc', dest='required_distance', type=int, default=3)
            p.add_argument('--model', choices=('memory','ideal-boundary'), default='memory')
            p.add_argument('--strategy', choices=('random','resource','cegis','mixed','v02','v03'), default='cegis')
            p.add_argument('--search-version', choices=('0.2','0.3'), default='0.2')
            p.add_argument('--equivalence', choices=('raw','signature','structural'), default='structural')
            p.add_argument('--initial-population', type=int, default=6)
        if name in ('memory','search'):
            p.add_argument('--rounds',type=int,default=3); p.add_argument('--basis',choices=('X','Z'),default='Z')
            p.add_argument('--logical-index',type=int,default=0); p.add_argument('--noisy-input',action='store_true')
        if name=='memory': p.add_argument('--candidate')
        if name=='verify': p.add_argument('--witness',required=True)
        if name=='decode': p.add_argument('--max-weight',type=int,default=1); p.add_argument('--max-combinations',type=int,default=100000)
        if name in ('search','faults','spectrum'):
            p.add_argument('--max-weight',type=int,choices=tuple(range(1,7)),default=3)
            p.add_argument('--max-combinations',type=int,default=2000000); p.add_argument('--idles',action='store_true')
    args=parser.parse_args(argv)
    try:
        path=Path(args.input)
        if args.command=='frontier':
            groups={}
            for file in sorted(path.glob('*.json')) if path.is_dir() else [path]:
                d=json.loads(file.read_text(encoding='utf-8'))
                if isinstance(d,dict) and 'code_input_hash' in d and 'frontier' in d:
                    config=d['configuration'];version=d.get('schema_version')
                    key=json.dumps([d['code_input_hash'],d.get('fault_model','repeated_noisy_memory'),d.get('memory_configuration'),config.get('idles'),config.get('target_dc',config.get('required_distance')),version,config.get('equivalence')],sort_keys=True)
                    selected=[d['records'][i-1] for i in d['frontier']] if version=='0.3' else d['frontier']
                    groups.setdefault(key,[]).extend(selected)
            if not groups: raise ValueError('No search-result JSON objects found')
            out={}
            for h,rs in groups.items():
                settings=json.loads(h)
                if settings[-2]=='0.3':
                    from .search.malignant import malignant_dominates
                    out[h]=[a for a in rs if not any(malignant_dominates(b,a,settings[-1]) for b in rs if b is not a)]
                else:out[h]=frontier(rs)
        else:
            d=json.loads(path.read_text(encoding='utf-8'))
            if args.command in ('validate','generate','memory','search'):
                code=StabilizerCode.from_dict(d)
                if args.command=='validate': out=dict(**code.metrics(),logicals=[[str(a),str(b)] for a,b in logical_basis(code)])
                elif args.command=='generate': out=[dict(architecture_id=c.id,candidate=c.to_dict(),circuit=build(code,c).to_dict()) for c in generate(code,args.budget,args.seed)]
                elif args.command=='memory':
                    from .circuits.memory import MemoryConfig,build_memory
                    from .architectures.candidate import Candidate
                    candidate=Candidate.from_dict(json.loads(Path(args.candidate).read_text(encoding='utf-8'))) if args.candidate else next(generate(code,1))
                    out=build_memory(code,candidate,MemoryConfig(args.rounds,args.basis,args.logical_index,args.noisy_input)).to_dict()
                elif args.model=='ideal-boundary':
                    if args.search_version=='0.3' or args.strategy in ('v02','v03'):
                        raise ValueError('V0.3 search requires the repeated-memory model')
                    if args.max_weight>3: raise ValueError('Legacy ideal-boundary search supports at most weight three')
                    out=search(code,args.budget,args.seed,args.max_weight,args.max_combinations,idles=args.idles,required_distance=args.required_distance)
                else:
                    from .circuits.memory import MemoryConfig
                    if args.search_version=='0.3' or args.strategy in ('v02','v03'):
                        from .search.malignant import MalignantConfig,run_malignant_search
                        strategy='v03' if args.strategy=='cegis' else args.strategy
                        out=run_malignant_search(code,MemoryConfig(args.rounds,args.basis,args.logical_index,args.noisy_input),
                            MalignantConfig(budget=args.budget,seed=args.seed,strategy=strategy,target_dc=args.required_distance,
                                max_weight=args.max_weight,max_combinations=args.max_combinations,idles=args.idles,
                                initial_population=args.initial_population,equivalence=args.equivalence))
                    else:
                        from .search.cegis import SearchConfig,run_search
                        out=run_search(code,MemoryConfig(args.rounds,args.basis,args.logical_index,args.noisy_input),
                                   SearchConfig(budget=args.budget,seed=args.seed,strategy=args.strategy,target_dc=args.required_distance,
                                                max_weight=args.max_weight,max_combinations=args.max_combinations,idles=args.idles,initial_population=args.initial_population))
            else:
                circuit=Circuit.from_dict(d)
                if args.command=='evaluate': out=resources(circuit)
                elif args.command=='verify':
                    from .faults.verification import verify_witness
                    w=json.loads(Path(args.witness).read_text(encoding='utf-8')); out=verify_witness(circuit,w.get('witness',w))
                elif args.command=='decode':
                    from .decoding.minimum_weight import BoundedMinimumWeightDecoder,decoder_failures
                    ss=signatures(circuit); dec=BoundedMinimumWeightDecoder().fit(ss,args.max_weight,args.max_combinations)
                    out=dict(training_completed_through=dec.completed_through,**decoder_failures(ss,dec,args.max_weight,args.max_combinations))
                elif args.command=='spectrum':
                    from .faults.spectrum import malignant_spectrum
                    out,_=malignant_spectrum(circuit,signatures(circuit,args.idles),args.max_weight,args.max_combinations)
                else:
                    out=search_faults(circuit,signatures(circuit,args.idles),args.max_weight,args.max_combinations)
                    if out['witness']:
                        from .faults.verification import verify_witness
                        out['independent_verification']=verify_witness(circuit,out['witness'])
        text=json.dumps(out,indent=2)
        if args.output:
            output=Path(args.output); output.parent.mkdir(parents=True,exist_ok=True); output.write_text(text+'\n',encoding='utf-8')
        else: print(text)
    except (ValueError,KeyError,OSError) as exc: parser.error(str(exc))

if __name__=='__main__': main()
