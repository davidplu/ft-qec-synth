"""Conservative resource-removal labels and whole-class diagnostic statistics.

These diagnostics do not tune or alter the prospectively frozen search.
"""
from .search import protection_audit as pareto_removal_audit
from .certification import METRICS, evaluate, SignatureCache, fingerprint, independent_audit, classify
from .circuits import build_design,validate_ideal
from .operators import compressions
from ..evaluation.resources import resources
from ..faults.search import search_faults
from ..faults.verification import verify_witness


def strict_minimality(audit, parent_resources):
    """A lower value in any metric prevents an unqualified minimality label.

    A surviving tradeoff is still Pareto eligible; local protection necessity
    is a different question from local resource dominance.
    """
    cheaper_valid=False; cheaper_unknown=False
    for removal in audit['removals']:
        cheaper=any(removal['child']['resources'][m] < parent_resources[m] for m in METRICS)
        removal['reduces_any_resource']=cheaper
        cheaper_valid |= cheaper and removal['classification']=='REMOVABLE'
        cheaper_unknown |= cheaper and removal['classification']=='UNKNOWN'
    return {**audit,'pareto_dominance_audit_label':audit['label'],
        'label':'NOT_LOCALLY_PROTECTION_MINIMAL' if cheaper_valid else 'UNKNOWN' if cheaper_unknown
                else 'LOCALLY_PROTECTION_MINIMAL',
        'minimality_definition':'no supported single edit lowers any resource while preserving target certification',
        'parent_resources':parent_resources}


def protection_audit(code,design,memory,config,cache=None):
    cache=cache or SignatureCache()
    parent,c=constraint_evaluation(code,design,memory,config,cache)
    if parent['region']!='VALID': raise ValueError('Minimality audit requires certified valid parent')
    rows=[]
    for child,op,feature in compressions(design,c,memory.rounds):
        rec,cc=constraint_evaluation(code,child,memory,config,cache,parent['circuit_hash'])
        if rec['region']=='VALID':
            independent=independent_audit(rec,cc,config.target_dc)
            if not independent['verified']: raise ArithmeticError('Removal exclusion failed')
            rec['independent_audit']=independent; necessity='REMOVABLE'
        elif rec['region']=='INVALID': necessity='PROVABLY_NECESSARY_WITHIN_TESTED_MODEL'
        elif rec['region']=='INVALID_STRUCTURE': necessity='EMPIRICALLY_NECESSARY'
        else: necessity='UNKNOWN'
        rows.append({'operator':op,'feature':feature,'classification':necessity,'child':rec,
            'scope':'conditional on this surrounding architecture and fault model'})
    result={'parent':design.id,'label':'DIAGNOSTIC_PENDING','removals':rows,'global_optimality_claim':False,
        'mutation_vocabulary':'all supported single compressions; no pairs',
        'screening':'same native distance cap; omit diagnostic malignant class construction; independently audit every valid removal'}
    return strict_minimality(result,parent['resources'])


def constraint_evaluation(code,design,memory,config,cache=None,parent_hash=None):
    """The normal distance constraint stages without unused spectrum features."""
    c=build_design(code,design,memory); ideal=validate_ideal(c)
    rec={'architecture_id':design.id,'design':design.to_dict(),'resources':resources(c),
         'circuit_hash':fingerprint(c),'ideal_validation':ideal}
    if not ideal['verified']:
        rec.update(region='INVALID_STRUCTURE',bounds={'status':'INVALID_IDEAL_CIRCUIT','lower_bound':1,'upper_bound':None,'witness':None})
        return rec,c
    ss,delta=(cache or SignatureCache()).get(c,parent_hash)
    bounds=search_faults(c,ss,config.target_dc-1,config.max_combinations)
    rec.update(bounds=bounds,region=classify(bounds,config.target_dc),delta_screen=delta)
    if bounds['witness']:
        rec['witness_verification']=verify_witness(c.to_dict(),bounds['witness'])
        if not rec['witness_verification']['verified']: raise ArithmeticError('Removal witness replay failed')
    return rec,c


def class_eliminated(members, mapped_effects):
    """Entire observed class, with unresolved mappings reported as UNKNOWN.

    mapped_effects maps each parent singleton index to a child physical
    (location, detector bits, logical bits). A surviving malignant realization
    disproves elimination. Removed/ambiguous locations never receive credit.
    """
    incomplete=False
    for indices in members:
        group=[mapped_effects.get(i) for i in indices]
        if any(effect is None for effect in group): incomplete=True; continue
        if len({effect[0] for effect in group})!=len(group): incomplete=True; continue
        detector=logical=0
        for _,d,l in group: detector^=d; logical^=l
        if not detector and logical: return False
    return None if incomplete else True
