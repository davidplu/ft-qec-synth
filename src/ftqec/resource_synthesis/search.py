"""Bidirectional repair/compression with bounded boundary exploration."""
from dataclasses import dataclass, asdict, replace
from collections import defaultdict
import random, time
from ..architectures.generators import generate
from ..circuits.memory import MemoryConfig
from ..faults.analysis import CounterexampleAnalysis, analyze, transport_witness
from ..faults.spectrum import representative_witness
from ..faults.verification import replay
from ..search.repairs import targeted_repairs, random_proposal
from ..search.engine import software_commit
from .design import Design, basis_mutations
from .certification import SignatureCache, evaluate, independent_audit, METRICS
from .operators import compressions
from .circuits import build_design
from .pareto import Archives, frontier, minima, tiers, dominates
from ..evaluation.resources import resources


@dataclass(frozen=True)
class ResourceConfig:
    budget: int = 48
    seed: int = 10
    target_dc: int = 3
    initial_population: int = 6
    archive_cap: int = 12
    max_combinations: int = 200000
    strategy: str = 'repair_compress'
    basis_search: bool = True
    new_family: bool = True
    option_limit: int = 4
    certify_final: bool = True

    def __post_init__(self):
        if self.strategy not in ('repair_compress','repair_only'): raise ValueError('Unknown resource search strategy')
        if min(self.budget,self.initial_population,self.archive_cap,self.option_limit) < 1: raise ValueError('Positive limits required')
        if not 2 <= self.target_dc <= 4: raise ValueError('Independent certification supports targets 2..4')
        if self.max_combinations < 0: raise ValueError('Negative work cap')


class OperatorStatistics:
    def __init__(self): self.rows = defaultdict(lambda:dict(attempts=0,valid_survivors=0,dc_failures=0,
        unknown=0,invalid_structure=0,class_trials=0,class_eliminated=0,dc_gain=0,
        delta={m:0 for m in METRICS}))

    def observe(self,operator,parent,child,eliminated=None):
        r=self.rows[operator]; r['attempts']+=1
        r['valid_survivors']+=child['region']=='VALID'; r['dc_failures']+=child['region']=='INVALID'
        r['unknown']+=child['region']=='UNKNOWN'; r['invalid_structure']+=child['region']=='INVALID_STRUCTURE'
        if eliminated is not None: r['class_trials']+=1; r['class_eliminated']+=eliminated
        upper=parent['bounds'].get('upper_bound')
        r['dc_gain']+=upper is not None and child['bounds']['lower_bound']>upper
        for m in METRICS: r['delta'][m]+=child['resources'][m]-parent['resources'][m]

    def priority(self,operator):
        r=self.rows.get(operator)
        if not r: return (0,0)  # untried operators first, run-local learning only
        # Prefer lower measured QD cost per Laplace-smoothed class elimination.
        return (1,(1+r['delta']['QD']/r['attempts'])/((r['class_eliminated']+1)/(r['class_trials']+2)))

    def to_dict(self):
        return {op:{**r,'probability_eliminates_source_class_representative':r['class_eliminated']/r['class_trials'] if r['class_trials'] else None,
            'probability_raises_dc':r['dc_gain']/r['attempts'],
            'mean_delta':{m:v/r['attempts'] for m,v in r['delta'].items()},
            'mean_saved':{m:-v/r['attempts'] for m,v in r['delta'].items()}}
            for op,r in self.rows.items()}


def retain_valid(parent,child,target):
    """Rollback rule for a proposed protected incumbent replacement."""
    return child if child['region']=='VALID' and dominates(child,parent) else parent


def protection_audit(code,design,memory,config,cache=None):
    cache=cache or SignatureCache(); parent,c=evaluate(code,design,memory,config.target_dc,config.max_combinations,cache)
    if parent['region']!='VALID': raise ValueError('Minimality audit requires certified valid parent')
    rows=[]; unresolved=False; cheaper_valid=False
    for child,op,feature in compressions(design,c,memory.rounds):
        row,cc=evaluate(code,child,memory,config.target_dc,config.max_combinations,cache,parent['circuit_hash'])
        cheaper=dominates(row,parent)
        if row['region']=='INVALID':
            necessity='PROVABLY_NECESSARY_WITHIN_TESTED_MODEL'  # independently replayed violating witness
        elif row['region']=='INVALID_STRUCTURE': necessity='EMPIRICALLY_NECESSARY'
        elif row['region']=='VALID':
            audit=independent_audit(row,cc,config.target_dc)
            if not audit['verified']: raise ArithmeticError('Removal exclusion audit failed')
            necessity='REMOVABLE'; cheaper_valid |= cheaper
        else: necessity='UNKNOWN'; unresolved |= cheaper
        rows.append({'operator':op,'feature':feature,'classification':necessity,'cheaper':cheaper,
            'child':row,'scope':'conditional on this surrounding architecture and fault model'})
    label='NOT_LOCALLY_PROTECTION_MINIMAL' if cheaper_valid else 'UNKNOWN' if unresolved else 'LOCALLY_PROTECTION_MINIMAL'
    return {'parent':parent['architecture_id'],'label':label,'mutation_vocabulary':'all compressions(design), single supported edits',
        'global_optimality_claim':False,'removals':rows}


def _repair_options(parent,circuit,design,cache,rng,config):
    options=[]; spectrum=parent.get('malignant_spectrum') or {}; classes=spectrum.get('classes',[])[:config.option_limit]
    ss,_=cache.get(circuit)
    analyses=[]
    if parent.get('counterexample_analysis'): analyses.append(CounterexampleAnalysis(**parent['counterexample_analysis']))
    for cls in classes:
        w=representative_witness(circuit,ss,cls)
        analyses.append(analyze(circuit,w,ss))
    for analysis in analyses:
        for candidate,provenance in targeted_repairs(design.candidate,analysis,rng):
            options.append((replace(design,candidate=candidate),provenance.repair_operator,
                            {'source_counterexample_id':analysis.counterexample_id,'kind':'REPAIR'}))
    # Repair omissions by restoring one measured epoch; repairs can undo compressions.
    for omission in design.omitted_checks:
        options.append((replace(design,omitted_checks=tuple(x for x in design.omitted_checks if x!=omission)),
                        'restore_syndrome_measurement',{'kind':'REPAIR'}))
    for omission in design.omitted_operations:
        options.append((replace(design,omitted_operations=tuple(x for x in design.omitted_operations if x!=omission)),
                        'restore_physical_operation',{'kind':'REPAIR'}))
    if config.basis_search:
        options.extend((d,op,{'kind':'BASIS','basis_parent':design.candidate.generating_basis}) for d,op in basis_mutations(circuit.code,design,config.option_limit))
    if config.new_family and design.family!='verified_cat':
        options.append((replace(design,family='verified_cat',shared_flags=False,omitted_operations=(),merged_records=()),
                        'switch_to_verified_cat',{'kind':'FAMILY'}))
    # Guarantee bounded exploration of the new design variables, rather than
    # burying them behind a long list of flag repairs.
    exploratory=[o for o in options if o[2]['kind'] in ('BASIS','FAMILY')]
    repairs=[o for o in options if o[2]['kind'] not in ('BASIS','FAMILY')]
    return repairs[:3]+exploratory+repairs[3:]


def run_resource_search(code,memory=MemoryConfig(),config=ResourceConfig(),initial=None):
    started=time.perf_counter(); rng=random.Random(config.seed); cache=SignatureCache()
    initial=list(initial) if initial is not None else [Design(a) for a in generate(code,min(config.initial_population,config.budget),config.seed)]
    if not initial or len(initial)>config.budget: raise ValueError('Invalid initial population')
    archives=Archives(config.target_dc,config.archive_cap); records=[]; circuits={}; by_id={}; queues={}; evaluated={}
    repair_stats=OperatorStatistics(); compression_stats=OperatorStatistics(); considered=set(); frontier_history=[]
    for step in range(config.budget):
        parent=None; op='initial_population'; provenance={'kind':'INITIAL'}
        if step<len(initial): design=initial[step]
        else:
            valid=archives.valid if config.strategy=='repair_compress' else []
            invalid=[r for r in records if r['region'] in ('INVALID','UNKNOWN')]
            # Preserve neutral malignant progress, then diversify across the best archive.
            def repair_key(r):
                spec=r.get('malignant_spectrum') or {}; layer=spec.get('layers',{}).get(str(r['bounds']['lower_bound']),{})
                count=layer.get('class_count')
                return (-r['bounds']['lower_bound'],count is None,count if count is not None else 10**12,r['resources']['QD'])
            pool=valid if valid and (step%3!=0 or not invalid) else sorted(invalid,key=repair_key)[:config.archive_cap]
            if not pool: pool=records[-config.archive_cap:]
            parent=pool[(step-len(initial))%len(pool)]; pdesign=Design.from_dict(parent['design'])
            if parent['architecture_id'] not in queues:
                pc=circuits[parent['architecture_id']]
                if parent['region']=='VALID' and config.strategy=='repair_compress':
                    opts=[]
                    for d,name,feature in compressions(pdesign,pc,memory.rounds):
                        predicted=resources(build_design(code,d,memory))
                        # Resource attribution drives generic predicted savings, not certification.
                        savings=parent['resources']['QD']-predicted['QD']
                        opts.append((-savings,name,feature,d))
                    opts.sort(key=lambda x:(x[0],x[1],x[2]))
                    options=[(d,name,{'kind':'COMPRESSION','feature':feature}) for _,name,feature,d in opts]
                    exploratory=[]
                    if config.basis_search: exploratory += [(d,name,{'kind':'BASIS'}) for d,name in basis_mutations(code,pdesign,config.option_limit)]
                    if config.new_family and pdesign.family!='verified_cat':
                        exploratory += [(replace(pdesign,family='verified_cat',shared_flags=False,omitted_operations=(),merged_records=()),'switch_to_verified_cat',{'kind':'FAMILY'})]
                    options=options[:3]+exploratory+options[3:]
                elif parent['region']=='VALID':
                    # Pure repair-only ablation: retain all existing protection.
                    options=[]
                    for i,order in enumerate(pdesign.candidate.orders):
                        if len(pdesign.candidate.flag_intervals[i])>=4: continue
                        flags=list(pdesign.candidate.flag_intervals); flags[i]=flags[i]+((0,len(order)),)
                        options.append((replace(pdesign,candidate=replace(pdesign.candidate,flag_intervals=tuple(flags))),
                                        'add_protection_to_valid',{'kind':'REPAIR'}))
                else:
                    options=_repair_options(parent,pc,pdesign,cache,rng,config)
                    options.sort(key=lambda opt:repair_stats.priority(opt[1]))
                unique={}
                for option in options: unique.setdefault(option[0].id,option)
                queues[parent['architecture_id']]=list(unique.values())
            q=queues[parent['architecture_id']]
            while q and q[0][0].id in considered: q.pop(0)
            if q: design,op,provenance=q.pop(0)
            else:
                candidate,_=random_proposal(pdesign.candidate,rng)
                if config.strategy=='repair_only' and parent['region']=='VALID':
                    candidate=pdesign.candidate
                design=replace(pdesign,candidate=candidate); op='random_local_mutation'; provenance={'kind':'RANDOM'}
        considered.add(design.id)
        if design.id in evaluated:
            rec={**evaluated[design.id],'runtime_seconds':0.0}; circuit=circuits[design.id]; cached=True
        else:
            rec,circuit=evaluate(code,design,memory,config.target_dc,config.max_combinations,cache,
                                 parent['circuit_hash'] if parent else None)
            evaluated[design.id]=rec; circuits[design.id]=circuit; cached=False
        rec={**rec,'evaluation_index':step+1,'cached_evaluation':cached,
            'elapsed_seconds':time.perf_counter()-started,
            'provenance':{**provenance,'operator':op,'parent_id':parent['architecture_id'] if parent else None,
                          'parent_evaluation':parent['evaluation_index'] if parent else None}}
        if parent:
            eliminated=None
            if parent['bounds'].get('witness') and rec['ideal_validation']['verified']:
                mapped,reason=transport_witness(circuits[parent['architecture_id']],circuit,parent['bounds']['witness'])
                if mapped:
                    v=replay(circuit.to_dict(),mapped); eliminated=bool(v['detector_outcomes'] or not v['logical_coset'])
                rec['source_witness_transport']={'reason':reason,'eliminated':eliminated}
            stat=compression_stats if provenance['kind']=='COMPRESSION' else repair_stats
            stat.observe(op,parent,rec,eliminated)
            rec['incumbent_replacement']=retain_valid(parent,rec,config.target_dc)['architecture_id'] if parent['region']=='VALID' else None
        records.append(rec); by_id[design.id]=rec; archives.update(rec)
        frontier_history.append({'evaluation':step+1,**archives.to_dict(),'minima':minima(archives.valid)})
    valid=frontier([r for r in records if r['region']=='VALID'])
    audits=[]
    if config.certify_final:
        for r in valid:
            audit=independent_audit(r,circuits[r['architecture_id']],config.target_dc)
            if not audit['verified']: raise ArithmeticError('Final independent certification failed')
            audits.append({'architecture_id':r['architecture_id'],**audit})
    return {'schema_version':'0.4','software_version':'0.4.0','software_git_commit':software_commit(),
        'objective':'resource Pareto minimization subject to certified target circuit distance',
        'code':code.to_dict(),'code_input_hash':code.input_hash,'configuration':asdict(config),
        'memory_configuration':asdict(memory),'seed':config.seed,
        'fault_model':'ideal encoded input; noisy mandatory extraction rounds; physical product readout; no idle faults',
        'initial_population_ids':[d.candidate.id for d in initial],
        'initial_design_ids':[d.id for d in initial],'evaluation_slots':len(records),
        'records':records,'archives':archives.to_dict(),'distance_conditioned_frontiers':tiers(records),
        'frontier':[r['architecture_id'] for r in valid],'frontier_history':frontier_history,
        'summary':{'target_reached':bool(valid),'minima_at_target':minima(valid),
                   'valid_candidates':sum(r['region']=='VALID' for r in records)},
        'repair_statistics':repair_stats.to_dict(),'compression_statistics':compression_stats.to_dict(),
        'independent_final_audits':audits,'runtime_seconds':time.perf_counter()-started}
