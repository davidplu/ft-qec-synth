"""Separate final-audit closure, preserving original bounded descent output."""
from dataclasses import asdict
from ..resource_synthesis.design import Design
from .descent import descend
from .staged import Budget


def complete(code,memory,records,frontier_ids,target,used_work=0,work_limit=20000000,evaluation_limit=128):
    unique={r['architecture_id']:r for r in records}
    parents=[unique[i] for i in frontier_ids]
    shared={(code.input_hash,str(memory),target,r['architecture_id']):r for r in unique.values()}
    budget=Budget(max(0,work_limit-used_work))
    result=descend(code,memory,parents,target,budget,evaluation_limit=evaluation_limit,shared=shared)
    return dict(descent=result,additional_certification_budget=asdict(budget),
                prior_used_work=used_work,combined_used_work=used_work+budget.used)
