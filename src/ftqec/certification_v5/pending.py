"""Finite neighbor inventory without certifying or consuming design evaluations."""
from ..resource_synthesis.design import Design
from ..resource_synthesis.operators import compressions
from ..resource_synthesis.circuits import build_design
from ..evaluation.resources import resources

def inventory(code,memory,row):
    from .canonical import normalize
    design=Design.from_dict(row['design']);c=build_design(code,design,memory);pending={}
    for child,operator,feature in compressions(design,c,memory.rounds):
        if operator=='remove_redundant_terminal_verification':continue
        child=normalize(child)
        if child.id in pending:continue
        actual=resources(build_design(code,child,memory))
        if any(actual[m]<row['resources'][m] for m in ('Q','D','QD','two_q_gates')):
            pending[child.id]=dict(child_id=child.id,operator=operator,feature=feature,resources=actual)
    return list(pending.values())
