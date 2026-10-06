"""Remove set-order aliases and reuse only exactly identical physical circuits."""
from dataclasses import replace,asdict
from types import FunctionType
from copy import deepcopy
import json
from ..resource_synthesis.design import Design
from ..resource_synthesis.circuits import build_design
from ..resource_synthesis.certification import fingerprint
from . import descent as module
from .staged import Budget


def normalize(design):
    return replace(design,omitted_checks=tuple(sorted(set(design.omitted_checks))),
        omitted_operations=tuple(sorted(set(design.omitted_operations),key=lambda x:json.dumps(x))),
        omitted_terminal=tuple(sorted(set(design.omitted_terminal))))


def complete(code,memory,records,frontier_ids,target,used_work=0,work_limit=20000000,evaluation_limit=1024):
    aliases={};canonical={};physical={};hits=0
    for row in records:
        d=normalize(Design.from_dict(row['design']));c=build_design(code,d,memory);h=fingerprint(c)
        if h!=row['circuit_hash']:raise ArithmeticError('Set-order normalization changed physical circuit')
        aliases[row['architecture_id']]=d.id;r=deepcopy(row)
        r.update(architecture_id=d.id,design=d.to_dict(),canonical_source_id=row['architecture_id'])
        if d.id not in canonical or r['bounds']['lower_bound']>canonical[d.id]['bounds']['lower_bound']:canonical[d.id]=r
        if r['region'] in ('VALID','INVALID','INVALID_STRUCTURE'):physical.setdefault((h,target),r)
    shared={(code.input_hash,str(memory),target,i):r for i,r in canonical.items()}
    parents=list({aliases[i]:canonical[aliases[i]] for i in frontier_ids}.values())
    budget=Budget(max(0,work_limit-used_work));original_ops=module.compressions;original_constraint=module.constraint
    def operations(design,circuit,rounds):
        return [(normalize(child),op,feature) for child,op,feature in original_ops(design,circuit,rounds)]
    def constraint(code,design,memory,target,budget,cache,parent_hash=None):
        nonlocal hits
        c=build_design(code,design,memory);h=fingerprint(c);key=(h,target)
        if key in physical:
            hits+=1;r=deepcopy(physical[key]);source=r['architecture_id']
            r.update(architecture_id=design.id,design=design.to_dict(),candidate=design.candidate.to_dict(),
                certificate_reused_from=source,runtime_seconds=0.0,
                provenance=dict(kind='EXACT_PHYSICAL_CERTIFICATE_REUSE',source_id=source))
            r.pop('phase_seconds',None)
            return r,c
        r,c=original_constraint(code,design,memory,target,budget,cache,parent_hash)
        if r['region'] in ('VALID','INVALID','INVALID_STRUCTURE'):physical[key]=deepcopy(r)
        return r,c
    # Scoped dependency injection without mutating the module's global registry.
    globals_copy={**module.__dict__,'compressions':operations,'constraint':constraint}
    run=FunctionType(module.descend.__code__,globals_copy,'canonical_descent',module.descend.__defaults__)
    result=run(code,memory,parents,target,budget,evaluation_limit=evaluation_limit,shared=shared)
    from .pending import inventory
    final_rows={r['architecture_id']:r for r in result['records']}
    for i in result['frontier']:
        audit=result['audits'][i]
        if audit['label']=='UNRESOLVED_MINIMALITY' and 'remaining_edit_ids' not in audit:
            neighbors=inventory(code,memory,final_rows[i])
            audit.update(remaining_edit_ids=[r['child_id'] for r in neighbors],
                         pending_inventory=neighbors,inventory_only=True)
    return dict(descent=result,additional_certification_budget=asdict(budget),prior_used_work=used_work,
        combined_used_work=used_work+budget.used,source_aliases=aliases,physical_certificate_cache_hits=hits,
        normalization='sort only omitted check/operation/terminal sets; verify exact circuit hash',
        independent_scope='all returned finalists; conclusive physical certificates reused only under identical full circuit hash and target')
