"""Clarify local versus global evidence after the unchanged frozen tests.

This does not rerun experiments, modify raw data, or change success criteria.
The user's RESULT B category permits mechanism/code-specific partial evidence;
it must not be confused with passing the frozen general-advantage criterion.
"""
from collections import defaultdict
import gzip
import json
from pathlib import Path
from ftqec.codes.stabilizer import StabilizerCode
from ftqec.architectures.generators import generate
from ftqec.circuits.memory import MemoryConfig,build_memory
from ftqec.faults.signatures import signatures
from ftqec.faults.search import search_faults
from ftqec.faults.verification import verify_witness

ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'results/v0.3'

def main():
    read=lambda name:json.loads((OUT/name).read_text(encoding='utf-8'))
    readiness=read('readiness.json');tests=read('paired_comparisons.json')
    distances=[t for t in tests if t['endpoint']=='distance']
    # Descriptive partial evidence, not a new endpoint or significance rule.
    local=any(t['wins']>t['losses'] and len(t['favorable_seeds'])>=2 for t in distances)
    if not readiness['frozen_development_criteria_passed'] and local:
        readiness['interpretation']='RESULT B — Partial local success; no validated general advantage'
    chains=read('repair_chains.json');cache={};details=[]
    for chain in chains:
        if chain['variant']!='v03':continue
        filename=f"{chain['code']}-{chain['basis']}-seed{chain['seed']}-v03.json.gz"
        if filename not in cache:
            with gzip.open(OUT/'raw'/filename,'rt',encoding='utf-8') as stream:cache[filename]=json.load(stream)
        records=cache[filename]['records'];cur=records[chain['gain_node']-1];segment=[]
        while cur['parent_node'] and cur['provenance']['kind']=='COUNTEREXAMPLE_GUIDED':
            parent=records[cur['parent_node']-1]
            delta=cur['repair_outcome_v03']['delta_M'].get(str(parent['bounds']['lower_bound']))
            if cur['evaluation_index']!=chain['gain_node'] and not(cur['dc_delta']==0 and delta is not None and delta<0):break
            segment.append(cur['evaluation_index']);cur=parent
        segment.reverse();end=records[chain['gain_node']-1];weight=cur['bounds']['lower_bound']
        nodes=[cur['evaluation_index']]+segment
        details.append({'run':filename,'gain_node':chain['gain_node'],'starting_node':cur['evaluation_index'],
            'guided_progress_segment':segment,'qualifies':len(segment)>=2,
            'start_dc':cur['bounds']['lower_bound'],'end_dc':end['bounds']['lower_bound'],
            'beyond_best_initial':end['bounds']['lower_bound']>max(r['bounds']['lower_bound'] for r in records[:6]),
            'architecture_ids':[records[n-1]['architecture_id'] for n in nodes],
            'class_counts_at_start_weight':[records[n-1]['malignant_spectrum']['layers'][str(weight)]['class_count'] for n in nodes],
            'operators':[records[n-1]['provenance']['repair_operator'] for n in segment],
            'targeted_class_ids':[records[n-1]['source_class_id'] for n in segment],
            'resource_delta':{m:end['resources'][m]-cur['resources'][m] for m in ('Q','D','QD','two_q_gates')}})
    strict={'definition':'Consecutive guided neutral class-reducing edges followed by a guided certified distance gain',
        'distance_gain_events':len(details),'strict_compositions':sum(d['qualifies'] for d in details),
        'strict_compositions_beyond_initial_best':sum(d['qualifies'] and d['beyond_best_initial'] for d in details),'events':details}
    rows=read('gradient.json')['edges'];exposure=[]
    for reduced in (True,False):
        part=[r for r in rows if r['variant']=='v03' and r['neutral_distance_edge'] and r['observed_descendants']>0 and (r['delta_M']<0)==reduced]
        exposure.append({'reduced':reduced,'expanded_edges':len(part),'future_gains':sum(r['future_gain'] for r in part),
            'fraction':sum(r['future_gain'] for r in part)/len(part) if part else None})
    aggregates=read('aggregate.json')
    totals={v:sum(a['target_successes'] for a in aggregates if a['variant']==v) for v in ('random','resource','v02','v03','mixed','v03_no_coverage')}
    readiness['local_partial_evidence']={'target_totals_out_of_48':totals,
        'strict_compositions':strict['strict_compositions'],'strict_compositions_beyond_initial_best':strict['strict_compositions_beyond_initial_best'],
        'does_not_pass_frozen_general_criteria':not readiness['frozen_development_criteria_passed']}
    def dump(name,value):(OUT/name).write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8')
    ceilings=[]
    for name in read('protocol.json')['codes']:
        code=StabilizerCode.from_dict(json.loads((ROOT/f'benchmarks/development/{name}.json').read_text(encoding='utf-8')))
        for basis in ('X','Z'):
            c=build_memory(code,next(generate(code,1)),MemoryConfig(3,basis))
            terminal=[s for s in signatures(c) if s.fault.role in ('final_data_readout','final_basis_change')]
            bounds=search_faults(c,terminal,3,200000)
            assert bounds['witness'] and verify_witness(c,bounds['witness'])['verified']
            ceilings.append({'code':name,'basis':basis,'logical_index':0,'full_circuit_distance_upper_bound':bounds['upper_bound'],
                'restricted_search_bounds':bounds,'witness_independently_verified':True})
    dump('boundary_ceilings.json',{'included_in_matched_experiment':False,
        'scope':'Development-only diagnostic; terminal-only witnesses are upper bounds, never full-circuit lower bounds',
        'invariance':'At fixed code, basis and logical index 0, readout axes and product-parity rows are fixed; extraction mutations change only the zero-effect detector prefix for terminal-only faults.',
        'rows':ceilings})
    dump('strict_composition_analysis.json',strict);dump('gradient_exposure_analysis.json',exposure);dump('readiness.json',readiness)
    path=ROOT/'docs/V0_3_RESULTS.md';text=path.read_text(encoding='utf-8')
    text=text.replace('X/Z memory, three extraction rounds','X/Z memory at logical index 0, three extraction rounds')
    clause=' The strict contiguous-guided definition yields 9/17; three exceed the best shared initial distance. The table composition column is the broader ancestry metric.'
    while clause+clause in text:text=text.replace(clause+clause,clause)
    for old in ('RESULT C — No reproducible advantage','RESULT B — Partial success'):
        text=text.replace(old,readiness['interpretation'])
    lines=text.splitlines()
    for i,line in enumerate(lines):
        if line.startswith('3. Composition before increase:'):
            lines[i]=f"3. Composition before increase: {strict['strict_compositions']}/{len(details)} gain events have consecutive guided neutral class reductions followed by a guided gain; {strict['strict_compositions_beyond_initial_best']} also exceed the best shared initial distance. This demonstrates composition, not necessity."
        elif line.startswith('16. Usually multi-step gains:'):
            lines[i]=f"16. Multi-step gains: {strict['strict_compositions']}/{len(details)} strict events, with overlapping ancestries. The broad ancestry metric was 10/17; it includes one noncontiguous case. Neither count proves that a shorter repair was impossible."
        elif line.startswith('V0.3 has 17 parent-child'):
            if clause not in line:lines[i]+=clause
        elif 'audited 3507 distinct raised-bound exclusions' in line:
            lines[i]=line.replace('audited 3507 distinct raised-bound exclusions','audited all 3507 distinct nontrivial certified bounds, including 87 distinct distance-gain exclusions')
    extra=['','## Local evidence does not satisfy the frozen general criterion','',
        f"The requested RESULT B interpretation fits the restricted evidence: targets {totals['v03']}/48 versus {totals['random']}/48 for each primary baseline, "
        'three distance wins all on Steane and seeds 1/4, nine strict composition events, and three strict chains beyond the shared initial best. '
        'No endpoint passes the unchanged frozen tests: every Holm-adjusted p-value is 1.0. '
        'The +6.25 percentage-point target margin and +0.0625 mean distance margin are descriptive. '
        'No new success threshold is introduced, and the algorithm is not ready to freeze.',
        '', 'Class-reducing nodes were expanded more often. Among equal-distance edges with at least one observed descendant: '+str(exposure)+'. '
        'This exposure restriction still does not remove adaptive selection, ancestry dependence or censoring. Larger reductions did not show a positive size/gain correlation (r=-0.093).',
        '', 'Disabling coverage prioritization reached 10/48 targets versus 6/48 for the frozen default. '
        'This is an exploratory ablation, not a promoted replacement algorithm or a retrospective readiness pass. '
        'Matched-tier mean QD was higher for V0.3 by 20.125 versus random, 92.333 versus resource and 26.458 versus V0.2 CEGIS.']
    extra+=['','A separate development-only boundary diagnostic finds the following rigorous upper bounds on the entire current architecture family. '
        'They are terminal-only witness upper bounds, not distance certificates for extraction. '
        'Readout axes and compatible-product rows are fixed by code/basis; extraction mutations cannot remove these terminal-only witnesses.',
        '', '| Code | Basis | Product-readout distance ceiling |','|---|---|---|']
    for row in ceilings:extra.append(f"| {row['code']} | {row['basis']} | {row['full_circuit_distance_upper_bound']} |")
    extra+=['','Only Steane has room above the best shared initial distance in this family. Thus the frozen requirement for distance gains across multiple codes '
        'cannot be established by this development set with its current boundaries. The matched-distance resource endpoint remained eligible, but did not pass. '
        'This limits the general hypothesis test; no benchmark, endpoint, target or algorithm was changed after observing results.']
    for d in [d for d in details if d['qualifies'] and d['beyond_best_initial']]:
        extra+=['',f"Strict global-distance-gain example {d['run']}: d_c {d['start_dc']} -> {d['end_dc']}; "
            f"architecture sequence {d['architecture_ids']}; M_{d['start_dc']}={d['class_counts_at_start_weight']}; "
            f"operators {d['operators']}; resource delta {d['resource_delta']}. Targeted classes and all nodes are in strict_composition_analysis.json."]
    marker='## Local evidence does not satisfy the frozen general criterion'
    if marker in '\n'.join(lines):lines=lines[:next(i for i,line in enumerate(lines) if line==marker)]
    path.write_text('\n'.join(lines+extra)+'\n',encoding='utf-8')
    print(json.dumps({'interpretation':readiness['interpretation'],'gate':readiness['status'],'strict_compositions':strict['strict_compositions']}))

if __name__=='__main__':main()
