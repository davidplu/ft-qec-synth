"""Audited frozen comparisons and explicit research questions, including nulls."""
from collections import Counter, defaultdict, OrderedDict
import gzip
import hashlib
import json
import math
from pathlib import Path
import statistics
import time
import jsonschema
from ftqec.codes.stabilizer import StabilizerCode
from ftqec.architectures.candidate import Candidate
from ftqec.circuits.memory import MemoryConfig, build_memory
from ftqec.faults.signatures import signatures
from ftqec.faults.search import witness
from ftqec.faults.verification import verify_witness
from ftqec.faults.batch_verification import verify_batch
from ftqec.faults.exclusion import verify_exclusion
from ftqec.faults.spectrum import boundary_class, classify, fault_features

ROOT=Path(__file__).resolve().parents[1]; OUT=ROOT/'results/v0.3'
PRIMARY=('random','resource','v02','v03','mixed')

def dump(name,value):
    (OUT/name).write_text(json.dumps(value,indent=2,allow_nan=False)+'\n',encoding='utf-8')

def sign_test(wins,losses):
    n=wins+losses
    return min(1.,2*sum(math.comb(n,k) for k in range(min(wins,losses)+1))/2**n) if n else 1.

def comparisons(index):
    tests=[]
    for baseline in ('random','resource','v02'):
        for endpoint in ('target_success','target_evaluations','distance','matched_QD'):
            values=[]
            for (code,basis,seed,variant),a in sorted(index.items()):
                if variant!='v03':continue
                b=index[(code,basis,seed,baseline)];sa=a['summary'];sb=b['summary']
                if endpoint=='target_success':difference=int(sa['target_reached'])-int(sb['target_reached'])
                elif endpoint=='target_evaluations':difference=(sb['evaluations_to_target'] or 33)-(sa['evaluations_to_target'] or 33)
                elif endpoint=='distance':difference=sa['best_dc_lower_bound']-sb['best_dc_lower_bound']
                else:
                    tier=min(sa['best_dc_lower_bound'],sb['best_dc_lower_bound'])
                    if tier<2:continue
                    difference=sb['best_resources_by_tier'][str(tier)]['QD']-sa['best_resources_by_tier'][str(tier)]['QD']
                values.append({'code':code,'basis':basis,'seed':seed,'difference_favoring_v03':difference})
            wins=sum(v['difference_favoring_v03']>0 for v in values);losses=sum(v['difference_favoring_v03']<0 for v in values)
            favorable=[v for v in values if v['difference_favoring_v03']>0]
            tests.append({'baseline':baseline,'endpoint':endpoint,'pairs':len(values),'wins':wins,'ties':len(values)-wins-losses,'losses':losses,
                'mean_margin':statistics.mean(v['difference_favoring_v03'] for v in values) if values else None,
                'p_two_sided':sign_test(wins,losses),'favorable_codes':sorted({v['code'] for v in favorable}),
                'favorable_seeds':sorted({v['seed'] for v in favorable}),'pairs_detail':values})
    ordered=sorted(tests,key=lambda t:t['p_two_sided']);previous=0
    for rank,t in enumerate(ordered):
        previous=max(previous,min(1,t['p_two_sided']*(len(tests)-rank)))
        t['holm_p']=previous
        t['passes_frozen_endpoint']=previous<=.05 and t['wins']>t['losses'] and len(t['favorable_codes'])>=2 and len(t['favorable_seeds'])>=3
    return tests

def gradient(records):
    children=defaultdict(list)
    for r in records:
        if r['parent_node']:children[r['parent_node']].append(r['evaluation_index'])
    rows=[]
    for r in records:
        if not r['parent_node']:continue
        parent=records[r['parent_node']-1];w=str(parent['bounds']['lower_bound'])
        delta=r['repair_outcome_v03']['delta_M'].get(w)
        if delta is None:continue
        stack=list(children[r['evaluation_index']]);desc=[]
        while stack:
            node=stack.pop();desc.append(records[node-1]);stack.extend(children[node])
        rows.append({'parent_node':r['parent_node'],'child_node':r['evaluation_index'],'delta_M':delta,
            'neutral_distance_edge':r['dc_delta']==0,'future_gain':any(d['bounds']['lower_bound']>r['bounds']['lower_bound'] for d in desc),
            'observed_descendants':len(desc),'remaining_slots':len(records)-r['evaluation_index'],
            'eventual_gain_from_parent_tier':r['dc_delta']>0 or any(d['bounds']['lower_bound']>parent['bounds']['lower_bound'] for d in desc)})
    return rows

def summarize_gradient(rows,neutral_only=False):
    rows=[r for r in rows if not neutral_only or r['neutral_distance_edge']]
    groups=[]
    for reduced in (True,False):
        part=[r for r in rows if (r['delta_M']<0)==reduced]
        groups.append({'reduced':reduced,'edges':len(part),'future_gains':sum(r['future_gain'] for r in part),
            'future_gain_fraction':sum(r['future_gain'] for r in part)/len(part) if part else None,
            'median_observed_descendants':statistics.median(r['observed_descendants'] for r in part) if part else None,
            'median_remaining_slots':statistics.median(r['remaining_slots'] for r in part) if part else None})
    # Pearson point-biserial, descriptive only; no independence/causality claim.
    reduced=[r for r in rows if r['delta_M']<0];xs=[-r['delta_M'] for r in reduced];ys=[int(r['future_gain']) for r in reduced]
    if len(xs)>1 and statistics.pstdev(xs)>0 and statistics.pstdev(ys)>0:
        mx=statistics.mean(xs);my=statistics.mean(ys)
        corr=sum((x-mx)*(y-my) for x,y in zip(xs,ys))/math.sqrt(sum((x-mx)**2 for x in xs)*sum((y-my)**2 for y in ys))
    else:corr=None
    return {'groups':groups,'reduction_magnitude_future_gain_correlation':corr,'causal':False,'neutral_edges_only':neutral_only}

def main():
    started=time.perf_counter();protocol=json.loads((OUT/'protocol.json').read_text(encoding='utf-8'))
    assert hashlib.sha256((ROOT/'docs/V0_3_HYPOTHESIS.md').read_text(encoding='utf-8').encode('utf-8')).hexdigest()==protocol['hypothesis_sha256']
    validator=jsonschema.Draft202012Validator(json.loads((ROOT/'docs/schemas/result-v0.3.schema.json').read_text(encoding='utf-8')))
    index={};groups=defaultdict(list);repair_rows=defaultdict(list);gradient_rows=[];chains=[];boundary=Counter();categories=Counter();turnover=Counter();trajectories=[]
    replayed=0;unique_verified=set();circuit_cache=OrderedDict();exclusions={};gain_exclusion_keys=set();min_checks=0;unknown_spectra=0;whole=Counter();audit_corrections=[];unsupported_architectures=set();boundary_classes=Counter();source_commits=set()
    files=sorted((OUT/'raw').glob('*.json.gz'))
    assert len(files)==480, f'Expected all 480 frozen runs, found {len(files)}'
    for run_index,file in enumerate(files):
        with gzip.open(file,'rt',encoding='utf-8') as stream:run=json.load(stream)
        validator.validate(run)
        source_commits.add(run['software_git_commit'])
        name=run['development_code'];basis=run['memory_configuration']['basis'];seed=run['configuration']['seed'];variant=run['experiment_variant']
        assert run['evaluation_slots']==32 and run['mutation_count']==26
        key=(name,basis,seed,variant)
        index[key]={'summary':run['summary'],'seconds':run['runtime_seconds'],'initial_population_ids':run['initial_population_ids']}
        groups[(name,basis,variant)].append((seed,run['summary'],run['runtime_seconds']))
        code=StabilizerCode.from_dict(run['code']);memory=MemoryConfig(**run['memory_configuration'])
        for r in run['records']:
            h=r['circuit_hash']
            if h not in circuit_cache:
                c=build_memory(code,Candidate.from_dict(r['candidate']),memory);ss=signatures(c,run['configuration']['idles'])
                circuit_cache[h]=(c,ss,{id(s):fault_features(c,s) for s in ss})
                if len(circuit_cache)>128:circuit_cache.popitem(last=False)
            c,ss,features=circuit_cache[h];circuit_cache.move_to_end(h)
            pending=[];pending_ids=set()
            if r['bounds'].get('witness'):
                w=r['bounds']['witness'];wid=hashlib.sha256((h+json.dumps(w,sort_keys=True)).encode()).hexdigest()
                if wid not in unique_verified:
                    assert verify_witness(c,w)['verified'];unique_verified.add(wid)
                replayed+=1;min_checks+=1
                boundary[boundary_class(w)[0]]+=1
            for layer in r['malignant_spectrum']['layers'].values():
                if layer['complete']:
                    assert layer['class_count']==len(layer['multiplicities'])
                    assert layer['raw_count']==sum(layer['multiplicities'].values())
            for cls in r['malignant_spectrum']['classes']:
                group=[ss[i] for i in cls['representative_indices']]
                assert classify(c,group,features).id==cls['id']
                w=witness(c,group).to_dict()
                family,repairability=boundary_class(w)
                boundary_classes[family]+=1
                if repairability=='UNSUPPORTED_REPAIR_CLASS':unsupported_architectures.add(h)
                wid=hashlib.sha256((h+json.dumps(w,sort_keys=True)).encode()).hexdigest()
                if wid not in unique_verified and wid not in pending_ids:
                    pending.append(w);pending_ids.add(wid)
                replayed+=1
            if pending:
                assert verify_batch(c,pending)['verified']
                unique_verified.update(pending_ids)
            if r['bounds']['lower_bound']>1:
                requested=r['bounds']['lower_bound']-1;ek=(h,requested)
                if ek not in exclusions:
                    exclusions[ek]=verify_exclusion(c,requested,run['configuration']['idles'])
                    assert exclusions[ek]['verified']
                if r.get('dc_delta',0)>0:
                    assert r['independent_exclusion']['verified'];gain_exclusion_keys.add(ek)
            if r.get('source_witness'):
                parent=run['records'][r['parent_node']-1];pc=build_memory(code,Candidate.from_dict(parent['candidate']),memory)
                assert verify_witness(pc,r['source_witness'])['verified'];replayed+=1
            if 'repair_outcome_v03' in r:
                o=r['repair_outcome_v03'];categories[(variant,o['category'])]+=1
                if r['provenance']['kind']=='COUNTEREXAMPLE_GUIDED':
                    repair_rows[(variant,r['provenance']['failure_class'],r['provenance']['repair_operator'])].append(r)
                    audited_whole=o['transported_source_class_eliminated']
                    if r.get('source_class_id'):
                        parent=run['records'][r['parent_node']-1]
                        complete=parent['malignant_spectrum']['layers'][str(r['source_witness']['fault_count'])]['complete']
                        if not complete and audited_whole is not None:
                            audit_corrections.append({'run':file.name,'node':r['evaluation_index'],
                                'raw_observed_members_eliminated':audited_whole,'audited_whole_class_eliminated':None,
                                'reason':'source class layer incomplete; observed members are not the whole class'})
                            audited_whole=None
                    whole[(variant,'unresolved' if audited_whole is None else 'eliminated' if audited_whole else 'survives')]+=1
                    if o['source_witness_eliminated'] is True:turnover[(variant,'source_eliminated')]+=1
                    turnover[(variant,'attempts')]+=1
            frontier_weight=str(r['bounds']['lower_bound']);layer=r['malignant_spectrum']['layers'].get(frontier_weight,{})
            unknown_spectra+=not layer.get('complete',False)
            trajectories.append({'code':name,'basis':basis,'seed':seed,'variant':variant,'node':r['evaluation_index'],
                'parent_node':r['parent_node'],'dc':r['bounds']['lower_bound'],'frontier_count':layer.get('class_count'),
                'raw_count':layer.get('raw_count'),'QD':r['resources']['QD'],'partial_progress':r['partial_progress'],
                'category':r.get('repair_outcome_v03',{}).get('category')})
        gradient_rows.extend([{**row,'code':name,'basis':basis,'seed':seed,'variant':variant} for row in gradient(run['records'])])
        chains.extend([{**ch,'code':name,'basis':basis,'seed':seed,'variant':variant} for ch in run['distance_gain_chains']])
        print(json.dumps({'validated_runs':run_index+1,'witness_instances':replayed}),flush=True)
        dump('audit_progress.json',{'validated_runs':run_index+1,'total_runs':len(files),'witness_instances':replayed})
    for (name,basis,seed,variant),run in index.items():
        assert run['initial_population_ids']==index[(name,basis,seed,'random')]['initial_population_ids']
    assert len(source_commits)==1
    aggregates=[]
    for (name,basis,variant),runs in sorted(groups.items()):
        runs.sort();aggregates.append({'code':name,'basis':basis,'variant':variant,'seeds':[s for s,_,_ in runs],
            'distance_distribution':[r['best_dc_lower_bound'] for _,r,_ in runs],
            'target_successes':sum(r['target_reached'] for _,r,_ in runs),'runs':len(runs),
            'target_evaluations':[r['evaluations_to_target'] for _,r,_ in runs],
            'best_resources_by_tier':[r['best_resources_by_tier'] for _,r,_ in runs],
            'successful_compositions':sum(r['successful_compositions'] for _,r,_ in runs),
            'mean_seconds':statistics.mean(t for _,_,t in runs)})
    comparisons_rows=comparisons(index)
    passed={b:any(t['passes_frozen_endpoint'] for t in comparisons_rows if t['baseline']==b) for b in ('random','resource','v02')}
    success=all(passed.values())
    ops=[]
    for (variant,failure,op),rows in sorted(repair_rows.items()):
        gains=[r for r in rows if r['repair_outcome_v03']['category'] in ('CLASS_ELIMINATION','MULTI_CLASS_IMPROVEMENT')]
        comparable=[r for r in rows if r['repair_outcome_v03']['counts_comparable']]
        costs=[r['QD_per_class_eliminated'] for r in gains if r['QD_per_class_eliminated'] is not None]
        ops.append({'variant':variant,'failure_class':failure,'operator':op,'attempts':len(rows),
            'complete_count_comparisons':len(comparable),'net_class_successes':len(gains),
            'success_fraction':len(gains)/len(rows),'mean_QD_per_class_eliminated':statistics.mean(costs) if costs else None,
            'mean_resource_delta':{m:statistics.mean(r['resource_delta'][m] for r in rows) for m in ('Q','D','QD','two_q_gates')}})
    gradient_summary={v:summarize_gradient([r for r in gradient_rows if r['variant']==v],True) for v in protocol['variants']}
    gradient_summary['all_v03_edges']=summarize_gradient([r for r in gradient_rows if r['variant']=='v03'])
    interpretation='RESULT A — Strong success' if success else 'RESULT B — Partial success' if any(t['passes_frozen_endpoint'] for t in comparisons_rows) else 'RESULT C — No reproducible advantage'
    reasons=[]
    if not success:reasons.append('V0.3 does not beat every required baseline under the frozen multiplicity-corrected, cross-code/cross-seed criteria.')
    reasons.append('Practical throughput at held-out code size has not been established; only development codes were run.')
    reasons.append('Pure product-readout boundary failures remain unsupported.')
    verification=json.loads((OUT/'verification.json').read_text(encoding='utf-8'))
    assert verification['passed']>=90 and verification['failures']==verification['errors']==verification['skipped']==0
    readiness={'status':'NOT_READY_FOR_HELD_OUT','interpretation':interpretation,'frozen_development_criteria_passed':success,
        'baseline_endpoint_passes':passed,'reasons':reasons,'held_out_runs':0,'external_architecture_searches':0,
        'algorithm_freeze_created':False,'tests':verification,'witness_instances_verified':replayed,
        'unique_witnesses_independently_replayed':len(unique_verified),'distance_gain_exclusions_verified':len(gain_exclusion_keys),
        'all_certified_bound_exclusions_verified':len(exclusions),'frozen_algorithm_commit':next(iter(source_commits)),
        'distinct_architectures_with_unsupported_boundary_classes':len(unsupported_architectures)}
    dump('aggregate.json',aggregates);dump('paired_comparisons.json',comparisons_rows);dump('operator_statistics.json',ops)
    dump('gradient.json',{'summary':gradient_summary,'edges':gradient_rows});dump('repair_chains.json',chains)
    dump('repair_classifications.json',{'categories':[{'variant':v,'category':c,'count':n} for (v,c),n in sorted(categories.items())],
        'source_vs_whole_class':[{'variant':v,'outcome':c,'count':n} for (v,c),n in sorted(whole.items())],
        'source_elimination':[{'variant':v,'metric':m,'count':n} for (v,m),n in sorted(turnover.items())]})
    dump('trajectories.json',trajectories);dump('readiness.json',readiness)
    dump('audit_corrections.json',audit_corrections)
    dump('validation.json',{'raw_runs':len(files),'all_schema_valid':True,'witness_instances':replayed,'unique_witnesses':len(unique_verified),
        'minimum_distance_witnesses':min_checks,'all_bound_exclusion_audits':list(exclusions.values()),
        'unknown_frontier_spectrum_records':unknown_spectra,'boundary_witness_family_counts':dict(boundary),
        'boundary_class_instances':dict(boundary_classes),'distinct_unsupported_boundary_architectures':len(unsupported_architectures),
        'validation_seconds':time.perf_counter()-started,'hypothesis_unchanged':True})
    lines=['# V0.3 malignant-gradient research results','',f'**{interpretation}. NOT_READY_FOR_HELD_OUT.**','',
        'The prospective criteria in `V0_3_HYPOTHESIS.md` were committed before the final experiment. '
        'No post-result algorithm tuning was performed. Baseline v0.2.0 and its raw results remain intact.',
        '', '## Model and matched protocol','',
        'css4, noncss4, perfect5, Steane; X/Z memory, three extraction rounds, ideal encoded input, noisy gates/ancilla resets/readouts and physical product terminal readout. '
        'One optional additional noisy terminal round is available to every strategy. Six seeds 0–5, six shared initial candidates, 32 slots, 26 mutation slots, '
        '200000 certification and spectrum work entries. Ten variants, 480 runs, 15360 slots. '
        'Unknown/capped counts never guide as zeros. Exact lower bounds are independent of the heuristic.',
        '', '## All codes, seeds and strategies','',
        '| Code | Basis | Variant | d_c lower bounds, seeds 0–5 | Targets / 6 | Evaluations to target | Compositions | Mean seconds |',
        '|---|---|---|---|---|---|---|---|']
    for a in aggregates:lines.append(f"| {a['code']} | {a['basis']} | {a['variant']} | {a['distance_distribution']} | {a['target_successes']} | {a['target_evaluations']} | {a['successful_compositions']} | {a['mean_seconds']:.3f} |")
    lines+=['','## Frozen primary tests','',
        'Positive margins favor V0.3. QD is measured at the common attained tier >=2; unequal-quality failures are not hidden in that conditional metric. '
        'Unreached target gets 33 evaluations. Exact paired sign tests use non-ties, with Holm correction over all 12 endpoints. '
        'These are small development experiments; shared code/seed dependence limits generalization. Passing also requires favorable cases across two codes and three seeds.',
        '', '| Baseline | Endpoint | W/T/L | Mean margin | Holm p | Frozen pass |','|---|---|---|---|---|---|']
    for t in comparisons_rows:lines.append(f"| {t['baseline']} | {t['endpoint']} | {t['wins']}/{t['ties']}/{t['losses']} | {t['mean_margin']} | {t['holm_p']:.6g} | {t['passes_frozen_endpoint']} |")
    lines+=['','## Direct gradient and ancestry','',
        'Probabilities below use equal-distance parent-child edges and descendants observed within the remaining budget. '
        'They are censored, endogenous search trajectories, not causal probabilities or independent trials. '
        'Observation exposure and reduction-size correlation are saved in `results/v0.3/gradient.json`.',
        '', '| Variant | Count reduced: future gains / edges | Count not reduced: future gains / edges | Reduction-size correlation |',
        '|---|---|---|---|']
    for v,g in gradient_summary.items():
        a,b=g['groups'];lines.append(f"| {v} | {a['future_gains']}/{a['edges']} | {b['future_gains']}/{b['edges']} | {g['reduction_magnitude_future_gain_correlation']} |")
    vchains=[c for c in chains if c['variant']=='v03'];composed=[c for c in vchains if c['neutral_progress_steps'] and c['guided_steps']>1]
    lines+=['',f'V0.3 has {len(vchains)} parent-child distance-gain events; {len(composed)} have a multi-guided-repair ancestry containing neutral class progress. '
        'These events are not necessarily independent architectures or improvements beyond the shared initial best. Every gain ancestry and intermediate spectrum is saved in `repair_chains.json`.']
    for ch in (composed[:2] or vchains[:2]):
        lines+=['',f"Example {ch['code']} {ch['basis']} seed {ch['seed']}: nodes {ch['nodes']}; operators {ch['operators']}; "
            f"neutral progress steps {ch['neutral_progress_steps']}; added resources {ch['resource_delta']}."]
    lines+=['','## Repair-level evidence and resource costs','',
        'Mechanism-key disappearance, net count reduction, exact source removal and elimination of every transportable raw realization of a source class are separate measures. '
        'Unknown/ambiguous transport receives no class-elimination credit. Full operator/failure tables and QD-per-class costs are saved in `operator_statistics.json`.',
        f'An audit refined {len(audit_corrections)} raw whole-class diagnostic labels to unresolved because the parent enumeration was capped. '
        'Raw files are preserved. This reporting correction changes no selection, operator history, spectrum, certificate or frozen endpoint.',
        '', '| V0.3 operator | Failure class | Net class successes / attempts | Mean added QD | QD / eliminated class |','|---|---|---|---|---|']
    vops=sorted([o for o in ops if o['variant']=='v03'],key=lambda o:(-o['success_fraction'],-o['attempts'],o['operator']))
    for o in vops:lines.append(f"| {o['operator']} | {o['failure_class']} | {o['net_class_successes']}/{o['attempts']} | {o['mean_resource_delta']['QD']:.2f} | {o['mean_QD_per_class_eliminated']} |")
    timing=json.loads((OUT/'timing.json').read_text(encoding='utf-8'))
    lines+=['','## Ablations, runtime and limits','',
        'Raw, signature, structural, no-protection, arbitrary-order and no-coverage comparisons are all in the complete table above. '
        'No best definition is declared from local count reduction alone. Signature equivalence can collapse all malignant mechanisms to a single logical-effect class. '
        'All spectrum trajectories, beam survival/pruning reasons, ancestry and mutation coverage estimates are retained losslessly in compressed raw JSON. '
        'Exact circuit/signature/class caches serve duplicates; tiny mutations are reevaluated fully rather than assuming invalid local reuse.',
        '',f"Total wall time {timing['wall_seconds']:.3f}s; summed search time {timing['sum_search_seconds']:.3f}s; "
        f"{timing['slots']/timing['wall_seconds']:.3f} slots/s including output. Separate function profiling is saved. "
        f"Validation replayed {len(unique_verified)} unique witnesses ({replayed} reported instances) and audited {len(exclusions)} distinct raised-bound exclusions. "
        f"Tests: {verification['passed']} passed, zero skips. Held-out runs: zero."]
    distance_tests={t['baseline']:t for t in comparisons_rows if t['endpoint']=='distance'}
    def ablation_margin(v):
        pairs=[(index[(c,b,s,'v03')]['summary']['best_dc_lower_bound'],index[(c,b,s,v)]['summary']['best_dc_lower_bound']) for c in protocol['codes'] for b in protocol['bases'] for s in protocol['seeds']]
        return {'wins':sum(a>b for a,b in pairs),'ties':sum(a==b for a,b in pairs),'losses':sum(a<b for a,b in pairs)}
    neutral=gradient_summary['v03']['groups'];ranked=vops[:3]
    responses=[
        f"Useful gradient: neutral count-reduction edges yielded {neutral[0]['future_gains']}/{neutral[0]['edges']} later distance gains, versus {neutral[1]['future_gains']}/{neutral[1]['edges']} nonreducing edges. This is descriptive and does not establish general predictive utility.",
        f"Source versus whole class: V0.3 source eliminations {turnover[('v03','source_eliminated')]}/{turnover[('v03','attempts')]}; transported whole-class eliminated/surviving/unresolved counts {whole[('v03','eliminated')]}/{whole[('v03','survives')]}/{whole[('v03','unresolved')]}. Net new alternatives are separately counted.",
        f"Composition before increase: {len(composed)}/{len(vchains)} V0.3 gain ancestries contain multiple guided steps and a neutral progress step; existence is not necessity.",
        f"Progress protection: strongest-distance V0.3 versus no-protection W/T/L {ablation_margin('v03_no_protection')}; resource and target outcomes are in the complete matched table.",
        f"Best equivalence: structural versus raw W/T/L {ablation_margin('v03_raw')}; structural versus signature {ablation_margin('v03_signature')}. No universal best is established by tied or code-dependent results.",
        'Highest observed class-level operator fractions: '+str([(o['operator'],o['failure_class'],o['net_class_successes'],o['attempts']) for o in ranked])+'. Small denominators are not reliable universal rankings.',
        f"Coverage prioritization: V0.3 versus no-coverage distance W/T/L {ablation_margin('v03_no_coverage')}; prospective coverage is estimated, not certified elimination.",
        f"Boundary bottleneck: {len(unsupported_architectures)} distinct architectures contain an observed unsupported terminal class; minimum-witness family instances {dict(boundary)} across all variants. This counts mechanisms, not stochastic failure probabilities.",
        f"Against random: distance W/T/L {distance_tests['random']['wins']}/{distance_tests['random']['ties']}/{distance_tests['random']['losses']}; frozen endpoint pass {passed['random']}.",
        f"Against resource search: distance W/T/L {distance_tests['resource']['wins']}/{distance_tests['resource']['ties']}/{distance_tests['resource']['losses']}; frozen endpoint pass {passed['resource']}.",
        f"Against V0.2 CEGIS: distance W/T/L {distance_tests['v02']['wins']}/{distance_tests['v02']['ties']}/{distance_tests['v02']['losses']}; frozen endpoint pass {passed['v02']}.",
        'Quantitative margins: all 12 paired endpoints, conditional QD units, target evaluation differences and adjusted p-values are reported above and in paired_comparisons.json.',
        f"Cross-code/seed persistence: frozen endpoint success requires two favorable codes and three favorable seeds; full criteria passed={success}. Favorable codes/seeds are listed for each endpoint in paired_comparisons.json.",
        f"Ablation: arbitrary-order W/T/L {ablation_margin('v03_arbitrary')}; equivalence, protection and coverage margins above. No post-hoc tuning followed these results.",
        'Resource costs: per-operator added Q/D/QD/two-qubit gates, QD per class removed and every per-edge QD per distance tier are in raw records and operator_statistics.json. The resource frontier retains tradeoffs rather than allowing unlimited redundant rounds.',
        f"Usually multi-step gains: {len(composed)}/{len(vchains)} qualifying V0.3 gain events; overlapping ancestries and repeated cached architectures prevent interpreting this as a universal necessity.",
        'Unsupported mechanisms: destructive product-readout/basis-only failures and arbitrary incompatible non-CSS boundary readout. One noisy repeated extraction round is available for mixed boundary faults; it provides no ideal protection.',
        f"Core hypothesis: {interpretation}. Passing local spectrum tests or eliminating a source witness does not establish synthesis superiority.",
        'Algorithm freeze: no; all readiness conditions are not met. ALGORITHM_FREEZE.md is not created.',
        'NOT_READY_FOR_HELD_OUT. Reasons: '+' '.join(reasons)]
    lines+=['','## Explicit answers to the 20 research questions','']
    lines += [f'{i}. {answer}' for i,answer in enumerate(responses,1)]
    (ROOT/'docs/V0_3_RESULTS.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    from interpret_v03 import main as interpret
    interpret()
    print((OUT/'readiness.json').read_text(encoding='utf-8'))

if __name__=='__main__':main()
