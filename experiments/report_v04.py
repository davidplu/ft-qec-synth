"""Read-only V0.4 summaries and reproducible scientific trajectory SVGs."""
from pathlib import Path
from collections import Counter, defaultdict
import gzip, json, statistics, hashlib
from v04_development import ROOT,OUT,historical_check,assert_frozen,dump,SEEDS
from ftqec.resource_synthesis.certification import METRICS
from ftqec.resource_synthesis.pareto import frontier,minima
from ftqec.resource_synthesis.pareto import tiers


def load(path):
    with gzip.open(path,'rt',encoding='utf-8') as f: return json.load(f)


def summarize():
    freeze=assert_frozen(); rows=[]; runs={}; pooled=defaultdict(list); all_tiers=defaultdict(list)
    for path in sorted((OUT/'raw').glob('*.gz')):
        result=load(path); group,task,variant,seed=path.name[:-8].split('--')
        summary=result.get('resource_summary',result['summary'])
        row={'run':path.name,'group':group,'task':task,'variant':variant,'seed':int(seed),
             **summary,'search_seconds':result['runtime_seconds'],'wall_seconds':result['driver_wall_seconds']}
        rows.append(row); runs[path.name]=result
        fids=result.get('resource_frontier',result.get('frontier',[]))
        pooled[group,task,variant].extend(r for r in result['records'] if r['architecture_id'] in fids)
        all_tiers[group,task,variant].extend(result['records'])
    groups={}
    for group in sorted({r['group'] for r in rows}):
        groups[group]={}
        for variant in sorted({r['variant'] for r in rows if r['group']==group}):
            items=[r for r in rows if r['group']==group and r['variant']==variant]
            bytask={t:sum(r['target_reached'] for r in items if r['task']==t) for t in sorted({r['task'] for r in items})}
            groups[group][variant]={'runs':len(items),'targets':sum(r['target_reached'] for r in items),
                'targets_by_task':bytask,'median_search_seconds':statistics.median(r['search_seconds'] for r in items),
                'max_search_seconds':max(r['search_seconds'] for r in items)}
    comparisons={}
    for group in sorted(groups):
        auto='v04' if group=='primary' else 'repair_compress'
        baselines=('v03','resource','random','no_basis','no_family') if group=='primary' else ('repair_only',)
        for baseline in baselines:
            pairs=[]
            for a in [r for r in rows if r['group']==group and r['variant']==auto]:
                b=next((r for r in rows if r['group']==group and r['task']==a['task'] and r['seed']==a['seed'] and r['variant']==baseline),None)
                if b:
                    both=a['target_reached'] and b['target_reached']
                    dominance=None
                    if both:
                        ar,br=runs[a['run']],runs[b['run']]
                        afids=ar.get('resource_frontier',ar.get('frontier',[])); bfids=br.get('resource_frontier',br.get('frontier',[]))
                        af=frontier([r for r in ar['records'] if r['architecture_id'] in afids])
                        bf=frontier([r for r in br['records'] if r['architecture_id'] in bfids])
                        weak=lambda x,y:all(x['resources'][m]<=y['resources'][m] for m in METRICS)
                        dominance={'auto_covers_baseline_frontier':all(any(weak(x,y) for x in af) for y in bf),
                            'baseline_covers_auto_frontier':all(any(weak(y,x) for y in bf) for x in af)}
                    pairs.append({'task':a['task'],'seed':a['seed'],'auto_valid':a['target_reached'],'baseline_valid':b['target_reached'],
                        'dominance':dominance,
                        'ratio':{m:a['minima_at_target'][m]/b['minima_at_target'][m] if both else None for m in METRICS},
                        'saved':{m:b['minima_at_target'][m]-a['minima_at_target'][m] if both else None for m in METRICS}})
            comparisons[f'{group}:{auto}/{baseline}']={'pairs':pairs,'joint_valid':sum(p['auto_valid'] and p['baseline_valid'] for p in pairs),
                'validity_wins':sum(p['auto_valid'] and not p['baseline_valid'] for p in pairs),
                'validity_losses':sum(p['baseline_valid'] and not p['auto_valid'] for p in pairs),
                'median_ratios':{m:statistics.median(v) if (v:=[p['ratio'][m] for p in pairs if p['ratio'][m] is not None]) else None for m in METRICS},
                'mean_saved':{m:statistics.mean(v) if (v:=[p['saved'][m] for p in pairs if p['saved'][m] is not None]) else None for m in METRICS}}
    paretos=[]
    for (group,task,variant),rs in sorted(pooled.items()):
        f=frontier(rs); paretos.append({'group':group,'task':task,'variant':variant,'minima':minima(f),
            'points':[{'architecture_id':r['architecture_id'],'resources':r['resources'],'bounds':r['bounds'],
                       'design':r.get('design'),'candidate':r['candidate']} for r in f]})
    minimality=Counter(); removals=defaultdict(Counter); examples={}; audit_count=0
    for path in sorted((OUT/'minimality').glob('*.gz')):
        result=load(path)
        for audit in result['audits']:
            minimality[audit['label']]+=1; audit_count+=1
            for removal in audit['removals']:
                removals[removal['operator']][removal['classification']]+=1
                kind=removal['classification']
                if kind not in examples:
                    examples[kind]={'run':result['run'],'parent':audit['parent'],'operator':removal['operator'],
                        'feature':removal['feature'],'child':removal['child']}
    trajectories=[]
    for name,result in runs.items():
        if not any(token in name for token in ('--v04--','--repair_compress--')): continue
        valid=[r for r in result['records'] if r['region']=='VALID']
        if not valid: continue
        best=min(valid,key=lambda r:r['resources']['QD']); bynode={r['evaluation_index']:r for r in result['records']}
        chain=[]; node=best
        while node:
            chain.append({'evaluation':node['evaluation_index'],'architecture_id':node['architecture_id'],
                'region':node['region'],'distance_lower_bound':node['bounds']['lower_bound'],
                'upper_bound':node['bounds']['upper_bound'],'resources':node['resources'],'provenance':node['provenance']})
            node=bynode.get(node['provenance'].get('parent_evaluation'))
        trajectories.append({'run':name,'nodes':list(reversed(chain))})
    native_unknown=sum(r.get('region')=='UNKNOWN' for result in runs.values() for r in result['records'])
    primary=groups['primary'].get('v04',{})
    reliable_tasks=[t for t,n in primary.get('targets_by_task',{}).items() if n>=.8*len(SEEDS)]
    parent_map={t['task']:('steane7' if t.get('shared_parent') in ('steane7','two steane7 blocks') else t['name'])
                for t in freeze['tasks']}
    reliable_parents={parent_map[t] for t in reliable_tasks}
    materially_compressed=defaultdict(set)
    for key,c in comparisons.items():
        if key.startswith('overprotected:'):
            for pair in c['pairs']:
                if pair['ratio']['QD'] is not None and pair['ratio']['QD']<=.9:
                    materially_compressed[pair['task']].add(pair['seed'])
    good_compression=[t for t,seeds in materially_compressed.items() if len(seeds)>=2]
    tradeoffs=[p['task'] for p in paretos if p['group']=='primary' and p['variant']=='v04'
               and len({tuple(point['resources'][m] for m in METRICS) for point in p['points']})>=2]
    gates={'tests':None,'target_success':len(reliable_parents)>=3,
           'compression_material_multiple_parents':len(good_compression)>=2,
           'independent_audits':all(a['verified'] for result in runs.values() for a in result['independent_final_audits']),
           'meaningful_tradeoffs':len(set(tradeoffs))>=2,
           'primary_runtime':primary.get('median_search_seconds',float('inf'))<=120 and primary.get('max_search_seconds',float('inf'))<=600,
           'higher_tier_scaling_justified':False,'heldout_uncontaminated':True}
    testpath=OUT/'final_tests.json'
    if testpath.exists(): gates['tests']=json.loads(testpath.read_text())['passed']
    readiness='READY_FOR_HELD_OUT' if all(v is True for v in gates.values()) else 'NOT_READY_FOR_HELD_OUT'
    data={'algorithm_commit':freeze['algorithm_commit'],'historical_files_unchanged':historical_check(),
        'run_count':len(rows),'groups':groups,'comparisons':comparisons,'runs':rows,
        'paretos':paretos,'minimality':dict(minimality),'audited_frontier_nodes':audit_count,
        'necessity_by_operator':{k:dict(v) for k,v in removals.items()},'necessity_examples':examples,
        'native_unknown_records':native_unknown,'readiness':readiness,'readiness_gates':gates,
        'reliable_tasks':reliable_tasks,'reliable_parent_instances':sorted(reliable_parents),
        'material_compression_tasks':good_compression,'tradeoff_tasks':tradeoffs,
        'runtime_note':'Primary, bare/overprotected and prefix supplement ran concurrently; times include contention.'}
    dump(OUT/'aggregate.json',data); dump(OUT/'trajectories.json',trajectories)
    dump(OUT/'pareto_frontiers.json',paretos); dump(OUT/'readiness.json',{'status':readiness,'gates':gates})
    dump(OUT/'distance_conditioned_frontiers.json',[{'group':g,'task':t,'variant':v,'tiers':tiers(records)}
         for (g,t,v),records in sorted(all_tiers.items())])
    draw_trajectories(trajectories)
    print(json.dumps({'groups':groups,'comparisons':{k:{kk:vv for kk,vv in c.items() if kk!='pairs'} for k,c in comparisons.items()},
        'minimality':dict(minimality),'readiness':readiness,'gates':gates},indent=2))


def draw_trajectories(trajectories):
    # Standalone vector scientific figure, no plotting dependency or raster generation.
    import html
    selected=[]
    for group in ('bare','overprotected','primary'):
        candidates=[t for t in trajectories if t['run'].startswith(group+'--')]
        if candidates: selected.append(max(candidates,key=lambda t:len(t['nodes'])))
    w,h=1020,230*max(1,len(selected)); parts=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">',
        '<rect width="100%" height="100%" fill="white"/>',
        '<style>text{font-family:Arial,sans-serif;font-size:12px}.title{font-size:15px}</style>']
    for j,t in enumerate(selected):
        y0=j*230; parts.append(f'<text class="title" x="20" y="{y0+22}">{html.escape(t["run"])}</text>')
        for col,metric in enumerate(('Q','D','QD')):
            x0=50+col*330; nodes=t['nodes']; vals=[n['resources'][metric] for n in nodes]; vmax=max(vals)*1.1
            coords=[(x0+260*i/max(1,len(nodes)-1),y0+175-125*v/vmax) for i,v in enumerate(vals)]
            parts.append(f'<text x="{x0}" y="{y0+42}">{metric}; labels = certified tier</text>')
            parts.append(f'<path d="M{x0},{y0+50} V{y0+175} H{x0+260}" stroke="#333" fill="none"/>')
            for value in (0,round(vmax/2),round(vmax)):
                yy=y0+175-125*value/vmax
                parts.append(f'<text x="{x0-7}" y="{yy+4:.1f}" text-anchor="end">{value}</text>')
            parts.append('<polyline points="'+' '.join(f'{x:.1f},{y:.1f}' for x,y in coords)+'" stroke="#295caa" stroke-width="2" fill="none"/>')
            for i,((x,y),node) in enumerate(zip(coords,nodes)):
                color='#25874e' if node['region']=='VALID' else '#b74138'
                parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="4" fill="{color}"/><text x="{x-4:.1f}" y="{y-9:.1f}">{node["distance_lower_bound"]}</text>')
                if i in (0,len(nodes)-1):
                    anchor='start' if i==0 else 'end'
                    parts.append(f'<text x="{x-6:.1f}" y="{y0+192}" text-anchor="{anchor}">eval {node["evaluation"]}: {vals[i]}</text>')
    parts.append('</svg>'); (OUT/'trajectories.svg').write_text('\n'.join(parts),encoding='utf-8')
    # Also plot resources against certified distance tier, connecting ancestry.
    parts=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">',
           '<rect width="100%" height="100%" fill="white"/>',
           '<style>text{font-family:Arial,sans-serif;font-size:12px}.title{font-size:15px}</style>']
    for j,t in enumerate(selected):
        y0=j*230; parts.append(f'<text class="title" x="20" y="{y0+22}">{html.escape(t["run"])}</text>')
        for col,metric in enumerate(('Q','D','QD')):
            x0=50+col*330; nodes=t['nodes']; vmax=max(n['resources'][metric] for n in nodes)*1.1
            coords=[(x0+120*(n['distance_lower_bound']-1),y0+175-125*n['resources'][metric]/vmax) for n in nodes]
            parts.append(f'<text x="{x0}" y="{y0+42}">{metric} versus certified tier; labels = evaluation</text>')
            parts.append(f'<path d="M{x0},{y0+50} V{y0+175} H{x0+260}" stroke="#333" fill="none"/>')
            for value in (0,round(vmax/2),round(vmax)):
                yy=y0+175-125*value/vmax
                parts.append(f'<text x="{x0-7}" y="{yy+4:.1f}" text-anchor="end">{value}</text>')
            for tier in (1,2,3): parts.append(f'<text x="{x0+120*(tier-1)-3}" y="{y0+195}">{tier}</text>')
            parts.append('<polyline points="'+' '.join(f'{x:.1f},{y:.1f}' for x,y in coords)+'" stroke="#295caa" stroke-width="2" fill="none"/>')
            annotations={}; first_valid=next((i for i,n in enumerate(nodes) if n['region']=='VALID'),len(nodes)-1)
            for i,((x,y),node) in enumerate(zip(coords,nodes)):
                color='#25874e' if node['region']=='VALID' else '#b74138'
                parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="4" fill="{color}"/>')
                if i in (0,first_valid,len(nodes)-1): annotations.setdefault((round(x,1),round(y,1)),[]).append(node['evaluation'])
            for (x,y),evaluations in annotations.items():
                label='e'+'/'.join(map(str,dict.fromkeys(evaluations)))
                parts.append(f'<text x="{x+7:.1f}" y="{y+4:.1f}">{label}</text>')
    parts.append('</svg>'); (OUT/'distance_tier_trajectories.svg').write_text('\n'.join(parts),encoding='utf-8')

if __name__=='__main__': summarize()
