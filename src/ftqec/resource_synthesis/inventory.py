"""Inspectable basis topology and family contributions to returned frontiers."""
from .design import Design,basis_code
from .pareto import minima


def design_inventory(code,records):
    bases={}; families={}
    for r in records:
        d=Design.from_dict(r['design']); key='|'.join(d.candidate.generating_basis)
        if key not in bases:
            bases[key]={'generators':d.candidate.generating_basis,'metrics':basis_code(code,d).metrics(),
                        'architecture_ids':[],'resource_rows':[]}
        bases[key]['architecture_ids'].append(r['architecture_id']); bases[key]['resource_rows'].append(r)
        families.setdefault(d.family,[]).append(r)
    for value in bases.values():
        value['predicted_extraction_resource_minima']=minima(value.pop('resource_rows'))
    return {'bases':list(bases.values()),'families':{
        name:{'evaluated':len(rs),'valid':sum(r['region']=='VALID' for r in rs),
              'valid_minima':minima([r for r in rs if r['region']=='VALID'])} for name,rs in families.items()},
        'signed_group_policy':'positive products only; signed membership verified; physical logical observable fixed'}
