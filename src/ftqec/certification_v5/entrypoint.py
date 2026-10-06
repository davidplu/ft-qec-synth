"""Public V0.5 interface with separate final-audit closure and verification methods."""
import argparse,json,sys
from pathlib import Path
from dataclasses import asdict
from . import cli
from .canonical import complete
from .exact import certify
from .upper import terminal_witness
from .staged import unknown_frontier
from ..codes.stabilizer import StabilizerCode
from ..circuits.memory import MemoryConfig
from ..resource_synthesis.design import Design
from ..resource_synthesis.circuits import build_design,validate_ideal
from ..resource_synthesis.certification import SignatureCache,classify


def main(argv=None):
    args=list(sys.argv[1:] if argv is None else argv)
    if args and args[0]=='verify-certificate':
        p=argparse.ArgumentParser();p.add_argument('input');p.add_argument('-o','--output')
        a=p.parse_args(args[1:]);data=json.loads(Path(a.input).read_text())
        from ..circuits.model import Circuit
        from .evidence import verify
        result=verify(Circuit.from_dict(data['circuit']),data['bounds'])
        if a.output:Path(a.output).write_text(json.dumps(result,indent=2)+'\n')
        else:print(json.dumps(result,indent=2))
        if not result['verified']:raise SystemExit(1)
        return
    if args and args[0]=='certify':return certification(args[1:])
    if args and args[0]=='frontier':
        from ..resource_synthesis.cli import main as historical_cli
        return historical_cli(args)
    limit=1024
    for i,arg in enumerate(args):
        if arg.startswith('--final-audit-evaluations='):
            limit=int(arg.split('=',1)[1]);args.pop(i);break
        if arg=='--final-audit-evaluations':
            limit=int(args[i+1]);del args[i:i+2];break
    if limit<0:raise ValueError('Negative final audit limit')
    cli.main(args)
    if args and args[0]=='search':
        output=next((a.split('=',1)[1] for a in args if a.startswith('--output=')),None)
        if output is None:
            i=next(i for i,a in enumerate(args) if a in ('-o','--output'));output=args[i+1]
        path=Path(output);data=json.loads(path.read_text());code=StabilizerCode.from_dict(data['code'])
        memory=MemoryConfig(**data['memory_configuration']);target=data['configuration']['target_dc']
        work=data['certification_budget'];result=complete(code,memory,data['records'],data['frontier'],target,
            work['used'],work['limit'],limit)
        combined={r['architecture_id']:r for r in data['records']}
        combined.update({r['architecture_id']:r for r in result['descent']['records']})
        data.update(final_audit_completion=result,records=list(combined.values()),frontier=result['descent']['frontier'])
        data['archives']['VALID_PARETO']=data['frontier']
        data['archives']['UNKNOWN_PARETO']=[r['architecture_id'] for r in unknown_frontier(data['records'])]
        data['summary']['minima_at_target']=result['descent']['minima']
        from ..resource_synthesis.pareto import tiers
        data['distance_conditioned_frontiers']=tiers(data['records'])
        data['final_minimality']={i:result['descent']['audits'][i]['label'] for i in data['frontier']}
        path.write_text(json.dumps(data,indent=2,allow_nan=False)+'\n',encoding='utf-8')


def certification(argv):
    p=argparse.ArgumentParser(description='Bounded exact physical distance certification')
    p.add_argument('input');p.add_argument('--design',required=True);p.add_argument('-o','--output',required=True)
    p.add_argument('--target-dc',type=int,default=3);p.add_argument('--rounds',type=int,default=3)
    p.add_argument('--basis',choices=('X','Z'),default='Z');p.add_argument('--logical-index',type=int,default=0)
    p.add_argument('--work-limit',type=int,default=1048576);p.add_argument('--table-limit',type=int,default=250000)
    p.add_argument('--independent-method',choices=('auto','pair','sat','trellis'),default='auto')
    a=p.parse_args(argv);path=Path(a.output);path.parent.mkdir(parents=True,exist_ok=True)
    code=StabilizerCode.from_dict(json.loads(Path(a.input).read_text()));design=Design.from_dict(json.loads(Path(a.design).read_text()))
    c=build_design(code,design,MemoryConfig(a.rounds,a.basis,a.logical_index));ideal=validate_ideal(c)
    if not ideal['verified']:out=dict(region='INVALID_STRUCTURE',ideal_validation=ideal,circuit=c.to_dict())
    else:
        from .projection import certify as projection_certify,verify as projection_verify
        from .exact import FAULT_MODEL
        from hashlib import sha256
        try:projection=projection_certify(c)
        except ValueError:projection=dict(reason='product_readout_projection_unavailable')
        ss,_=SignatureCache().get(c)
        if projection.get('lower_bound',0)>=a.target_dc:
            lower=projection['lower_bound']
            b=dict(lower_bound=lower,upper_bound=None,status='LOWER_BOUND',excluded_through=lower-1,
                witness=None,combinations_examined=0,requested_weight=a.target_dc-1,
                fault_variants=len(ss),fault_locations=len({s.fault.location for s in ss}),
                certificate=dict(circuit_hash=projection['circuit_hash'],fault_inventory_hash=projection['fault_inventory_hash'],
                    fault_model_hash=sha256(FAULT_MODEL.encode()).hexdigest(),target=a.target_dc,
                    algorithm_version=projection['algorithm'],work_limit=a.work_limit,table_limit=a.table_limit,payload=projection))
        else:
            b=certify(c,ss,a.target_dc,a.work_limit,a.table_limit)
            if projection.get('lower_bound',0)>b['lower_bound']:
                b['native_exclusion_evidence']=dict(b)
                b['lower_bound']=projection['lower_bound'];b['excluded_through']=b['lower_bound']-1
                b['certificate']={**b['certificate'],'algorithm_version':projection['algorithm'],
                                  'payload':projection}
        upper=terminal_witness(c,ss)
        if upper['upper_bound'] is not None and (b['upper_bound'] is None or upper['upper_bound']<b['upper_bound']):
            b['upper_bound']=upper['upper_bound'];b['witness']=upper['witness']
        if b['upper_bound'] is not None and b['upper_bound']<b['lower_bound']:raise ArithmeticError('Contradictory distance evidence')
        b['status']='EXACT' if b['upper_bound']==b['lower_bound'] else 'UPPER_BOUND' if b['upper_bound'] is not None else b['status']
        through=b['lower_bound']-1;method=a.independent_method
        if method=='auto':method='projection' if projection.get('lower_bound',0)>=b['lower_bound'] else 'pair' if through<=4 else 'sat'
        if method=='projection':audit=projection_verify(c,projection)
        elif through<=2 and method=='pair':
            from .low_audit import exclude
            audit=exclude(c,through)
        elif method=='pair':
            from .pair_audit import exclusion
            audit=exclusion(c,through) if through<=4 else dict(verified=False,reason='pair_method_supports_through_four')
        elif method=='sat':
            try:
                from .sat_audit import exclusion
                audit=exclusion(c,through,model_path=path.with_suffix('.model.bin'))
            except ModuleNotFoundError:audit=dict(verified=False,reason='install_optional_sat_verification_dependency')
        else:
            from .independent import exclusion
            audit=exclusion(c,through)
        out=dict(bounds=b,region=classify(b,a.target_dc),independent_verification=audit,upper_evidence=upper,
                 independently_verified_target=bool(audit.get('verified') and b['lower_bound']>=a.target_dc),
                 projection_certificate=projection,circuit=c.to_dict(),ideal_validation=ideal)
    path.write_text(json.dumps(out,indent=2,allow_nan=False)+'\n',encoding='utf-8')


if __name__=='__main__':main()
