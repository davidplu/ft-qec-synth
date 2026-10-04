"""Report the frozen development comparison; no algorithm adaptation."""
from collections import defaultdict,Counter
import gzip,json,statistics,random
from compare_development_v2 import ROOT,OUT,BENCH,check_protocol,sign_permutation,holm,dump

def family(t):return 'simplex_css' if t['family']=='direct_sum' else t['family']

def parent_code(t):return 'steane7' if t['family']=='direct_sum' else t['shared_parent'] or t['name']

def bootstrap(pairs,tasks):
    rng=random.Random(20261004);families=sorted({family(tasks[p['task']]) for p in pairs})
    seeds=sorted({p['seed'] for p in pairs});table={(p['task'],p['seed']):p['difference'] for p in pairs}
    byfamily={f:sorted({p['task'] for p in pairs if family(tasks[p['task']])==f}) for f in families}
    values=[]
    for _ in range(2000):
        fs=rng.choices(families,k=len(families));ss=rng.choices(seeds,k=len(seeds))
        sample=[table[t,s] for f in fs for t in byfamily[f] for s in ss if (t,s) in table]
        if sample:values.append(statistics.mean(sample))
    values.sort()
    return [values[int(.025*(len(values)-1))],values[int(.975*(len(values)-1))]] if values else None

def main():
    m=check_protocol();tasks={t['task']:t for t in m['tasks']};runs={};summaries=[];composition=[];gradient=[];operators=defaultdict(lambda:Counter())
    independent_initial=json.loads((OUT/'final_initial_quality.json').read_text())
    independent_initial_target={(task,seed):any(x['target'] for x in independent_initial if x['task']==task and x['seed']==seed) for task in tasks for seed in m['final_seeds']}
    for path in sorted((OUT/'raw').glob('*.gz')):
        with gzip.open(path,'rt',encoding='utf-8') as f:r=json.load(f)
        t=r['development_task'];seed=r['configuration']['seed'];v=r['experiment_variant'];recs=r['records']
        init=recs[:6];target=tasks[t]['d_target'];best=r['summary']['best_dc_lower_bound']
        resources={str(tier):min(x['resources']['QD'] for x in recs if x['bounds']['lower_bound']>=tier) for tier in range(1,best+1)}
        row={'task':t,'code':tasks[t]['name'],'family':family(tasks[t]),'seed':seed,'variant':v,
             'target':int(r['summary']['target_reached']),'evaluations':r['summary']['evaluations_to_target'] or (m['evaluation_budget']+1),
             'distance':best,'qd_by_tier':resources,'seconds':r['runtime_seconds'],
             'initial_target':int(any(x['bounds']['lower_bound']>=target for x in init)),
             'independently_resolved_initial_target':int(independent_initial_target[t,seed]),
             'unique_candidates':r['unique_candidates_evaluated'],'memory':r.get('process_memory',{}),
             'certification_seconds':sum(x.get('fault_search_seconds',0) for x in recs if not x['cached_evaluation']),
             'signature_seconds':sum(x.get('signature_seconds',0) for x in recs if not x['cached_evaluation']),
             'spectrum_seconds':sum(x.get('spectrum_seconds',0) for x in recs if not x['cached_evaluation']),
             'complete_frontier_records':sum(x['malignant_spectrum']['layers'][str(x['bounds']['lower_bound'])]['complete'] for x in recs),
             'pretarget_incomplete_frontier_records':sum(x['bounds']['lower_bound']<target and not x['malignant_spectrum']['layers'][str(x['bounds']['lower_bound'])]['complete'] for x in recs),
             'certification_cap_records':sum(x['bounds'].get('reason')=='work_limit' for x in recs),
             'spectrum_cap_records':sum(any(not layer['complete'] and layer.get('reason')!='not_searched_above_frontier' for layer in x['malignant_spectrum']['layers'].values()) for x in recs),
             'combinations':sum(x['bounds'].get('combinations_examined',0) for x in recs if not x['cached_evaluation']),
             'file':path.name}
        weights=tasks[t]['d_initial'];initial_counts=[x['malignant_spectrum']['layers'][str(weights)].get('class_count') for x in init]
        measured=[x['malignant_spectrum']['layers'][str(weights)].get('class_count') for x in recs if x['malignant_spectrum']['layers'][str(weights)]['complete']]
        initial_measured=[c for c in initial_counts if c is not None]
        row['best_frontier_reduction']=min(initial_measured)-min(measured) if measured and initial_measured else None
        runs[t,seed,v]=[(x['elapsed_seconds'],x['bounds']['lower_bound']) for x in recs];summaries.append(row)
        # Full ancestry is used for descriptive mechanisms only.
        for x in recs:
            if not x['parent_node']:continue
            if x['provenance']['kind']=='COUNTEREXAMPLE_GUIDED':
                key=(v,x['provenance']['failure_class'],x['provenance']['repair_operator']);op=operators[key]
                op['attempts']+=1;op['source_eliminated']+=bool(x['repair_outcome_v03']['source_witness_eliminated'])
                op['complete_class_eliminated']+=x['repair_outcome_v03']['transported_source_class_eliminated'] is True
                op['net_class_reduction']+=x['repair_outcome_v03']['category'] in ('CLASS_ELIMINATION','MULTI_CLASS_IMPROVEMENT')
            parent=recs[x['parent_node']-1];delta=x['repair_outcome_v03']['delta_M'].get(str(parent['bounds']['lower_bound']))
            descendants=[]
            for y in recs[x['evaluation_index']:]:
                p=y['parent_node']
                while p and p!=x['evaluation_index']:p=recs[p-1]['parent_node']
                if p==x['evaluation_index']:descendants.append(y)
            if x.get('dc_delta')==0 and delta is not None:
                gradient.append({'task':t,'seed':seed,'variant':v,'node':x['evaluation_index'],'delta_M':delta,
                    'descendants':len(descendants),'future_gain':any(y['bounds']['lower_bound']>x['bounds']['lower_bound'] for y in descendants)})
            if x.get('dc_delta',0)>0:
                cur=parent;neutral=[]
                while cur['parent_node']:
                    before=recs[cur['parent_node']-1];d=cur['repair_outcome_v03']['delta_M'].get(str(before['bounds']['lower_bound']))
                    if cur['dc_delta']!=0 or d is None or d>=0:break
                    neutral.append(cur);cur=before
                chain=[cur]+list(reversed(neutral))+[x];guided=all(y['provenance']['kind']=='COUNTEREXAMPLE_GUIDED' for y in chain[1:])
                weight=cur['bounds']['lower_bound']
                composition.append({'task':t,'seed':seed,'variant':v,'gain_node':x['evaluation_index'],
                    'neutral_reductions':len(neutral),'observed_composition':bool(neutral),'strict_guided_composition':bool(neutral) and guided,
                    'nodes':[y['evaluation_index'] for y in chain],
                    'architecture_ids':[y['architecture_id'] for y in chain],
                    'M':[y['malignant_spectrum']['layers'][str(weight)]['class_count'] for y in chain],
                    'dc':[y['bounds']['lower_bound'] for y in chain],
                    'operators':[y['provenance']['repair_operator'] for y in chain[1:]],
                    'resource_delta':{metric:x['resources'][metric]-cur['resources'][metric] for metric in ('Q','D','QD')},
                    'beyond_initial_best':x['bounds']['lower_bound']>max(y['bounds']['lower_bound'] for y in init)})
    dump(OUT/'run_summaries.json',summaries);dump(OUT/'composition.json',composition);dump(OUT/'gradient.json',gradient)
    dump(OUT/'operator_statistics.json',[{'variant':k[0],'failure':k[1],'operator':k[2],**dict(v)} for k,v in sorted(operators.items())])
    primary=[s for s in summaries if s['variant'] in m['primary_variants']];table={(s['task'],s['seed'],s['variant']):s for s in primary};tests=[]
    for baseline in ('random','resource','v02'):
        for endpoint in ('target','evaluations','distance','qd'):
            pairs=[]
            for t in tasks:
                for seed in m['final_seeds']:
                    a=table[t,seed,'v03'];b=table[t,seed,baseline]
                    if endpoint=='qd':
                        tier=min(a['distance'],b['distance'])
                        if tier<2:continue
                        av=a['qd_by_tier'][str(tier)];bv=b['qd_by_tier'][str(tier)];d=bv-av
                    else:
                        av=a[endpoint];bv=b[endpoint];d=(bv-av) if endpoint=='evaluations' else av-bv
                    pairs.append({'task':t,'seed':seed,'difference':d,'a':av,'b':bv})
            seedmeans=[statistics.mean(p['difference'] for p in pairs if p['seed']==seed) for seed in m['final_seeds'] if any(p['seed']==seed for p in pairs)]
            familymeans=[statistics.mean(p['difference'] for p in pairs if family(tasks[p['task']])==f) for f in sorted({family(tasks[p['task']]) for p in pairs})]
            positive=[p for p in pairs if p['difference']>0];codeids={parent_code(tasks[p['task']]) for p in positive}
            mean=statistics.mean(p['difference'] for p in pairs) if pairs else None
            practical=(mean is not None and (mean>=.10 if endpoint=='target' else mean>=8 if endpoint=='evaluations' else mean>=.1 if endpoint=='distance' else statistics.mean(p['difference']/p['b'] for p in pairs)>=.10))
            tests.append({'baseline':baseline,'endpoint':endpoint,'pairs':len(pairs),'wins':len(positive),
                'ties':sum(p['difference']==0 for p in pairs),'losses':sum(p['difference']<0 for p in pairs),
                'mean_oriented_difference':mean,'effect_95pct_seed_family_bootstrap':bootstrap(pairs,tasks) if pairs else None,
                'p':sign_permutation(seedmeans),'family_block_sensitivity_p':sign_permutation(familymeans),
                'favorable_parent_codes':sorted(codeids),'favorable_families':sorted({family(tasks[p['task']]) for p in positive}),
                'favorable_seeds':sorted({p['seed'] for p in positive}),'practical_margin_passed':practical,
                'generalization_spread_passed':len(codeids)>=3 and len({family(tasks[p['task']]) for p in positive})>=2 and len({p['seed'] for p in positive})>=6})
    holm(tests)
    for t in tests:t['passes']=t['p_holm']<=.05 and t['mean_oriented_difference']>0 and t['practical_margin_passed'] and t['generalization_spread_passed']
    dump(OUT/'paired_comparisons.json',tests)
    aggregates=[]
    for task in tasks:
        for v in m['primary_variants']+m['secondary_ablations']:
            ss=[s for s in summaries if s['task']==task and s['variant']==v]
            aggregates.append({'task':task,'variant':v,'runs':len(ss),'targets':sum(s['target'] for s in ss),
                'initial_targets':sum(s['initial_target'] for s in ss),
                'independently_resolved_initial_targets':sum(s['independently_resolved_initial_target'] for s in ss),
                'mean_dc':statistics.mean(s['distance'] for s in ss),
                'mean_penalized_evaluations':statistics.mean(s['evaluations'] for s in ss),
                'mean_seconds':statistics.mean(s['seconds'] for s in ss),
                'slots_per_second':m['evaluation_budget']*len(ss)/sum(s['seconds'] for s in ss),
                'mean_complete_frontier_reduction':statistics.mean(s['best_frontier_reduction'] for s in ss if s['best_frontier_reduction'] is not None) if any(s['best_frontier_reduction'] is not None for s in ss) else None})
    dump(OUT/'aggregate.json',aggregates)
    alltable={(s['task'],s['seed'],s['variant']):s for s in summaries};ablations=[]
    for v in m['secondary_ablations']:
        for endpoint in ('target','distance','evaluations','qd'):
            ds=[]
            for task in tasks:
                for seed in m['secondary_ablation_seeds']:
                    a=alltable[task,seed,'v03'];b=alltable[task,seed,v]
                    if endpoint=='qd':
                        tier=min(a['distance'],b['distance'])
                        if tier<2:continue
                        d=b['qd_by_tier'][str(tier)]-a['qd_by_tier'][str(tier)]
                    else:d=b[endpoint]-a[endpoint] if endpoint=='evaluations' else a[endpoint]-b[endpoint]
                    ds.append(d)
            ablations.append({'ablation':v,'endpoint':endpoint,'paired_seeds':m['secondary_ablation_seeds'],
                'wins':sum(d>0 for d in ds),'ties':sum(d==0 for d in ds),'losses':sum(d<0 for d in ds),
                'mean_oriented_difference':statistics.mean(ds) if ds else None,'confirmatory':False})
    dump(OUT/'ablation_comparisons.json',ablations)
    characteristics=[]
    for task,t in tasks.items():
        weights=t['metrics']['weights'];overlaps=t['metrics']['overlaps']
        off=[overlaps[i][j] for i in range(len(overlaps)) for j in range(i)]
        ms=[layer[str(t['d_initial'])]['class_count'] for run in t['initial_malignant_spectra'] for layer in run if layer[str(t['d_initial'])]['complete']]
        characteristics.append({'task':task,'family':family(t),'shared_parent':t['shared_parent'],'n':t['n'],'k':t['k'],'css':t['css'],
            'mean_check_weight':statistics.mean(weights),'max_check_weight':max(weights),'mean_overlap':statistics.mean(off) if off else 0,
            'mean_degree':statistics.mean(t['metrics']['degrees']),'observed_mechanism_count':len(t.get('failure_mechanisms',{})),
            'mean_initial_classes':statistics.mean(ms) if ms else None,'calibrated_initial_target_frequency':t['initial_target_frequency'],
            'target_gap':t['d_target']-t['d_initial'],'boundary_headroom':t['boundary']['distance']-t['d_initial'],
            'v03_minus_random_target_success':statistics.mean(alltable[task,seed,'v03']['target']-alltable[task,seed,'random']['target'] for seed in m['final_seeds']),
            'v03_minus_random_distance':statistics.mean(alltable[task,seed,'v03']['distance']-alltable[task,seed,'random']['distance'] for seed in m['final_seeds'])})
    correlations=[]
    for feature in ('n','k','mean_check_weight','max_check_weight','mean_overlap','mean_degree','observed_mechanism_count','mean_initial_classes','boundary_headroom'):
        pairs=[(c[feature],c['v03_minus_random_target_success']) for c in characteristics if c[feature] is not None]
        xs=[p[0] for p in pairs];ys=[p[1] for p in pairs]
        mx=statistics.mean(xs);my=statistics.mean(ys);den=(sum((x-mx)**2 for x in xs)*sum((y-my)**2 for y in ys))**.5
        correlations.append({'feature':feature,'pearson':sum((x-mx)*(y-my) for x,y in pairs)/den if den else None,'task_count':len(pairs),'exploratory_only':True})
    dump(OUT/'exploratory_characteristics.json',{'tasks':characteristics,'correlations':correlations,'causal_claim':False})
    gradients=[]
    for v in m['primary_variants']:
        for expanded in (False,True):
            for reduced in (False,True):
                part=[g for g in gradient if g['variant']==v and (g['delta_M']<0)==reduced and (not expanded or g['descendants']>0)]
                gradients.append({'variant':v,'expanded_only':expanded,'reduced':reduced,'edges':len(part),'later_gains':sum(g['future_gain'] for g in part),
                                 'fraction':sum(g['future_gain'] for g in part)/len(part) if part else None})
    dump(OUT/'gradient_association.json',gradients)
    comp={v:{'gains':sum(c['variant']==v for c in composition),'compositions':sum(c['variant']==v and c['observed_composition'] for c in composition),
             'guided_compositions':sum(c['variant']==v and c['strict_guided_composition'] for c in composition),
             'beyond_initial_compositions':sum(c['variant']==v and c['observed_composition'] and c['beyond_initial_best'] for c in composition)} for v in m['primary_variants']}
    dump(OUT/'composition_summary.json',comp)
    checkpoints=[]
    for task in tasks:
        limit=statistics.median(s['seconds'] for s in primary if s['task']==task and s['variant']=='random')
        for fraction in (.25,.5,1):
            for v in m['primary_variants']:
                outcomes=[]
                for seed in m['final_seeds']:
                    available=[dc for elapsed,dc in runs[task,seed,v] if elapsed<=limit*fraction]
                    outcomes.append({'seed':seed,'slots_completed':len(available),'target':any(dc>=tasks[task]['d_target'] for dc in available),
                                     'best_dc':max(available,default=0)})
                checkpoints.append({'task':task,'variant':v,'random_median_seconds':limit,'fraction':fraction,'outcomes':outcomes})
    dump(OUT/'wall_clock_comparison.json',checkpoints)
    failures=[]
    pilots={p['task']:p for p in json.loads((OUT/'pilots.json').read_text())}
    for task in tasks:
        ss=[s for s in primary if s['task']==task]
        if not any(s['target'] for s in ss):failures.append({'task':task,'classification':'E_SEARCH_FAILED_DESPITE_CERTIFIED_REACHABLE_CANDIDATE',
            'alternative':'B_INSUFFICIENT_SEARCH_BUDGET remains possible; no impossibility inference','pilot':pilots[task]['status']})
    dump(OUT/'all_strategy_failures.json',failures)
    runtime=[]
    for task,t in tasks.items():
        ss=[s for s in primary if s['task']==task]
        runtime.append({'task':task,'n':t['n'],'check_count':len(t['metrics']['weights']),'rounds':3,'max_fault_weight':3,
            'evaluation_slots_per_sec':m['evaluation_budget']*len(ss)/sum(s['seconds'] for s in ss),
            'unique_architectures_per_sec':sum(s['unique_candidates'] for s in ss)/sum(s['seconds'] for s in ss),
            'examined_fault_combinations_per_sec':sum(s['combinations'] for s in ss)/sum(s['certification_seconds'] for s in ss) if sum(s['certification_seconds'] for s in ss) else None,
            'certification_seconds':sum(s['certification_seconds'] for s in ss),'spectrum_seconds':sum(s['spectrum_seconds'] for s in ss),
            'peak_working_set_bytes':max(s['memory'].get('peak_working_set_bytes',0) for s in ss)})
    dump(OUT/'runtime_scaling.json',runtime)
    validation=json.loads((OUT/'validation.json').read_text());verification=json.loads((OUT/'final_tests/verification.json').read_text())
    proxies=json.loads((OUT/'proxies.json').read_text()) if (OUT/'proxies.json').exists() else []
    practical=any(p['n']>=20 and p['evaluation_slots']==32 and p['seconds']<=1800 and 0<p['memory'].get('peak_working_set_bytes',0)<=2*1024**3 and p['independent_best_exclusion']['verified'] and p['independent_best_exclusion']['excluded_through']>=2 for p in proxies)
    advantage=all(any(t['passes'] and t['baseline']==b for t in tests) for b in ('random','resource','v02'))
    ready=advantage and practical and verification['successful'] and validation['verified'] and len(tasks)>=3
    reasons=[]
    if not advantage:reasons.append('Frozen reproducible advantage criterion failed.')
    if not practical:reasons.append('Frozen smaller-size runtime proxy gate failed or unresolved.')
    readiness={'status':'READY_FOR_HELD_OUT' if ready else 'NOT_READY_FOR_HELD_OUT','advantage_passed':advantage,
               'runtime_gate_passed':practical,'tests':verification,'reasons':reasons,'held_out_runs':0,
               'algorithm_unchanged':True,'benchmark_manifest_frozen':True,
               'limitation_categories':([] if advantage else ['ALGORITHM_LIMITATION','BENCHMARK_LIMITATION'])+
                                      (['COMPUTE_LIMITATION'] if not practical or any(s['pretarget_incomplete_frontier_records'] for s in primary) else [])+
                                      ['FAULT_MODEL_LIMITATION'],
               'category_explanation':'Reachable tasks separate search failure from impossible targets; family diversity and generator controls limit generality, work caps can suppress the class gradient, and fixed product readout rejects genuinely non-CSS candidates.'}
    dump(OUT/'readiness.json',readiness)
    write_report(m,aggregates,tests,comp,gradients,runtime,readiness,failures,proxies)
    print(json.dumps(readiness,indent=2))

def write_report(m,aggregates,tests,comp,gradients,runtime,readiness,failures,proxies):
    pool=json.loads((OUT/'candidate_pool.json').read_text());screen=json.loads((OUT/'screening.json').read_text());tasks=m['tasks']
    primary_names={t['name'] for t in tasks};families={family(t) for t in tasks};codes={parent_code(t) for t in tasks}
    lines=['# Development Suite 2 results','',readiness['status'], '',
        'The V0.3 runtime source and all original results are byte-identical to the pre-design freeze. New inputs are permanently development. No held-out input, architecture or resource count was used. Final seeds differ from calibration and pilots. All raw final runs, initial spectra, rejected candidates and reachability pilots are saved separately.','',
        'Selection follows DEVELOPMENT_V2_SELECTION_PROTOCOL.md and the prospectively committed structural pool extension. Manifest and hypothesis hashes are checked before every run. Candidate distances use explicit construction proofs or exhaustive Pauli checks; terminal ceilings use physical replay and exhaustive classical parity supports. A terminal-only distance is an upper bound on a full circuit, never its lower bound.','',
        'Distance claims concern the frozen chosen-basis logical-index-zero memory experiment. In k>1 tasks, protection of every encoded logical observable is not established. Circuit candidates still extract all supplied checks. Sign-flip tests assume symmetric/exchangeable seed-block differences under the null; they are not a randomized causal trial.','',
        f'Considered {len(pool)} code instances and {len(screen)} basis tasks. Selected {len(tasks)} tasks from {len(primary_names)} named check sets, {len(codes)} parent instances and {len(families)} underlying construction families. Non-CSS generator controls and direct sums have shared dependence. The suite does not establish generalization to arbitrary non-CSS stabilizer groups.','',
        '| Task | n,k | code d | initial | boundary | target | CSS representation |','|---|---|---:|---:|---:|---:|---|']
    for t in tasks:
        d=t['distance_certificate'];lines.append(f"| {t['task']} | {t['n']},{t['k']} | {d.get('construction_distance',d.get('distance',d.get('lower_bound')))} | {t['d_initial']} | {t['boundary']['distance']} | {t['d_target']} | {t['css']} |")
    lines+=['','Rejected/deferred candidate tasks:', '', '| Task | Screen | Difficulty |','|---|---|---|']
    for s in screen:
        if s['task'] not in {t['task'] for t in tasks}:lines.append(f"| {s['task']} | {s['classification']} | {s['difficulty']} |")
    lines+=['','Failure-mechanism coverage (sampled representatives):','','| Task | Observed mechanisms |','|---|---|']
    for t in tasks:lines.append('| '+t['task']+' | '+', '.join(f'{k}:{v}' for k,v in sorted(t.get('failure_mechanisms',{}).items()))+' |')
    lines+=['','Final strategy results use native frozen-engine bounds. Initial-target counts are retained, never removed after selection; independent resolution is a separate column. Ablation rows have three seeds, primary rows ten.','','| Task | Strategy | targets/runs | native initial targets | independent initial targets | mean d lower | penalized evaluations | seconds/run |','|---|---|---:|---:|---:|---:|---:|---:|']
    for a in aggregates:lines.append(f"| {a['task']} | {a['variant']} | {a['targets']}/{a['runs']} | {a['initial_targets']} | {a['independently_resolved_initial_targets']} | {a['mean_dc']:.2f} | {a['mean_penalized_evaluations']:.2f} | {a['mean_seconds']:.2f} |")
    lines+=['','Paired confirmatory tests. Positive difference favors V0.3; QD differences are absolute QD saved. Seed blocks contain all tasks, with family-block sensitivity and two-level bootstrap intervals. Small family counts sharply limit generalization.','','| Baseline | Endpoint | W/T/L | effect | 95% interval | Holm p | family sensitivity p | passes |','|---|---|---|---:|---|---:|---:|---|']
    for t in tests:lines.append(f"| {t['baseline']} | {t['endpoint']} | {t['wins']}/{t['ties']}/{t['losses']} | {t['mean_oriented_difference']} | {t['effect_95pct_seed_family_bootstrap']} | {t['p_holm']:.4f} | {t['family_block_sensitivity_p']:.4f} | {t['passes']} |")
    lines+=['','Observed composition is not proof that the repairs were necessary. Full ancestry, architecture IDs, M sequences, d sequences and resource changes are in composition.json.','','| Strategy | gain events | neutral-reduction compositions | strict guided | beyond initial compositions |','|---|---:|---:|---:|---:|']
    for v,c in comp.items():lines.append(f"| {v} | {c['gains']} | {c['compositions']} | {c['guided_compositions']} | {c['beyond_initial_compositions']} |")
    lines+=['','Expanded-node gradient association (observational, exposure-confounded):','','| Strategy | class reduction | edges | later gains | fraction |','|---|---|---:|---:|---:|']
    for g in gradients:
        if g['expanded_only']:lines.append(f"| {g['variant']} | {g['reduced']} | {g['edges']} | {g['later_gains']} | {g['fraction']} |")
    lines+=['','Runtime/scaling; examined-combination rates refer to bounded certification, not all possible combinations. Capped third-weight searches cannot establish completion. Wall-clock checkpoints include analysis overhead and are saved in wall_clock_comparison.json. Process peaks include earlier runs in the same driver process.','','| Task | n | checks | slots/s | unique arch/s | fault joins/s | peak MiB |','|---|---:|---:|---:|---:|---:|---:|']
    for r in runtime:lines.append(f"| {r['task']} | {r['n']} | {r['check_count']} | {r['evaluation_slots_per_sec']:.3f} | {r['unique_architectures_per_sec']:.3f} | {r['examined_fault_combinations_per_sec']} | {r['peak_working_set_bytes']/1024**2:.1f} |")
    lines+=['','Unrelated size proxies (runtime only):','','| Proxy | n | slots | seconds | best lower bound | peak MiB |','|---|---:|---:|---:|---:|---:|']
    for p in proxies:lines.append(f"| {p['name']} | {p['n']} | {p['evaluation_slots']} | {p['seconds']:.2f} | {p['best_dc']} | {p['memory'].get('peak_working_set_bytes',0)/1024**2:.1f} |")
    lines+=['','No projection is a held-out-code measurement. Proxy checks differ in connectivity/degeneracy and exact signatures, so equal n is not equal certification cost. Targets above the frozen tier and rigorous large-distance certification remain compute-limited.','',
            'All-strategy failures: '+json.dumps(failures)+'. Pilot witness existence distinguishes bounded search failure from impossible targets. No failed pilot proves unreachability.','',
            'Exploratory characteristics: task-wise effects and class spectra are saved. Parent-dependent representation controls, basis correlation and small family count prevent credible causal attribution to check weight, overlap, degeneracy or k. Do not promote an ablation after observing its performance.','',
            'Explicit final answers:','']
    boundary=[s for s in screen if s['classification']=='BOUNDARY_LIMITED'];easy=[s for s in screen if s['difficulty']=='TOO_EASY'];unknown=[s for s in screen if s['difficulty']=='UNREACHABLE/UNKNOWN' and s['classification']!='BOUNDARY_LIMITED']
    answers=[f'{len(pool)} candidate code instances ({len(screen)} basis tasks).',
        f'{len(boundary)} basis tasks of {len({s["name"] for s in boundary})} codes were boundary-limited; this counts at least one rejected basis, not necessarily rejection of the entire code.',
        f'{len(easy)} tasks were too easy/at their terminal ceiling. Certification-tier-limited cases are counted separately, not called easy.',
        f'{len(unknown)} screening tasks unresolved/deferred; bounded failed pilots remain unknown, never proven unreachable.',
        ', '.join(t['task'] for t in tasks)+'.',f'{len(families)} underlying families, k values '+str(sorted({t['k'] for t in tasks}))+', code distances '+str(sorted({t['distance_certificate'].get('construction_distance',t['distance_certificate'].get('distance')) for t in tasks}))+'. Shared-parent controls are explicit.',
        'Every admitted task has proved terminal headroom and a certified reachable target above the calibrated initial bound. New-seed initial successes are reported separately.',
        'Calibration target frequency is zero by the prospectively defined target rule; final initial-target counts appear in the strategy table.',
        'Passed frozen criterion versus RANDOM: '+str(any(t['passes'] for t in tests if t['baseline']=='random'))+'.',
        'Passed frozen criterion versus RESOURCE_GUIDED: '+str(any(t['passes'] for t in tests if t['baseline']=='resource'))+'.',
        'Passed frozen criterion versus V0.2 CEGIS: '+str(any(t['passes'] for t in tests if t['baseline']=='v02'))+'.',
        'Passing endpoints: '+str([(t['baseline'],t['endpoint']) for t in tests if t['passes']])+'. All descriptive endpoint effects and intervals are above.',
        'Favorable parent-code, family and seed sets are retained per endpoint in paired_comparisons.json; basis tasks are not independent codes.',
        'Statistical/practical meaning requires Holm significance, practical margin and spread simultaneously; see passes column. Few independent families constrain generalization.',
        'The expanded-node gradient fractions above are descriptive and confounded; they do not establish prediction out of sample or causality.',
        'Observed strict guided compositions: '+str(comp['v03'])+'. They do not prove necessity.',
        'No reliable causal predictor established; all code-characteristic analyses are exploratory and parent-correlated.',
        'Smaller-size frozen runtime gate passed: '+str(readiness['runtime_gate_passed'])+'. Proxy runtime is empirical; n31/n44 extrapolations are conditional, not certification promises.',
        'If advantage fails on these reachable tasks, algorithm/search-budget limitations remain; benchmark diversity, certification caps and fixed product readout remain additional limitations.',
        readiness['status']+'. '+ ' '.join(readiness['reasons'])]
    lines += [f'{i}. {a}' for i,a in enumerate(answers,1)]
    lines+=['','One next experiment: independently increase only the matched evaluation budget on this already-frozen suite, keeping targets, operators and certification caps fixed, to distinguish budget insufficiency from persistent guidance failure. This is a proposed future experiment, not a V0.4 implementation.']
    (ROOT/'docs/DEVELOPMENT_V2_RESULTS.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')

if __name__=='__main__':main()
