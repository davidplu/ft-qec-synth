"""Operator outcomes stratified by experiment group/variant and validity."""
from collections import defaultdict
import gzip,json
from v04_development import OUT,dump
from ftqec.resource_synthesis.certification import METRICS
from ftqec.resource_synthesis.inventory import design_inventory
from ftqec.codes.stabilizer import StabilizerCode

def main():
    stats={}; inventories=[]
    for path in sorted((OUT/'raw').glob('*.gz')):
        with gzip.open(path,'rt') as f: run=json.load(f)
        if run['schema_version']!='0.4': continue
        group,task,variant,seed=path.name[:-8].split('--')
        bynode={r['evaluation_index']:r for r in run['records']}
        inventories.append({'run':path.name,'inventory':design_inventory(StabilizerCode.from_dict(run['code']),run['records'])})
        for child in run['records']:
            prov=child['provenance']; parent=bynode.get(prov.get('parent_evaluation'))
            if parent is None: continue
            key=':'.join((group,variant,prov['kind'],prov['operator']))
            row=stats.setdefault(key,{'attempts':0,'valid_survivors':0,'dc_failures':0,'unknown':0,'invalid_structure':0,
                'all_saved':{m:0 for m in METRICS},'valid_saved':{m:0 for m in METRICS}})
            row['attempts']+=1; row['valid_survivors']+=child['region']=='VALID'; row['dc_failures']+=child['region']=='INVALID'
            row['unknown']+=child['region']=='UNKNOWN'; row['invalid_structure']+=child['region']=='INVALID_STRUCTURE'
            for m in METRICS:
                delta=parent['resources'][m]-child['resources'][m]
                row['all_saved'][m]+=delta
                if child['region']=='VALID': row['valid_saved'][m]+=delta
    for row in stats.values():
        row['mean_saved_all_attempts']={m:v/row['attempts'] for m,v in row.pop('all_saved').items()}
        row['mean_saved_valid_survivors']={m:v/row['valid_survivors'] if row['valid_survivors'] else None for m,v in row.pop('valid_saved').items()}
    dump(OUT/'operator_statistics.json',stats); dump(OUT/'design_inventory.json',inventories)

if __name__=='__main__': main()
