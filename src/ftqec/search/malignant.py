"""V0.3 bounded malignant-progress archive and compositional search.

Certification is delegated unchanged to the V0.2 fault engine. Malignant counts
are a separate exhaustive search objective, never a distance certificate.
"""
from dataclasses import dataclass, asdict, replace
from collections import defaultdict
import random
import time
from ..architectures.candidate import Candidate
from ..architectures.generators import generate
from ..circuits.memory import MemoryConfig
from ..faults.signatures import signatures
from ..faults.analysis import analyze, transport_witness
from ..faults.verification import replay, verify_witness
from ..faults.spectrum import malignant_spectrum, representative_witness, spectrum_delta, boundary_class
from ..serialization import json_native
from ..evaluation.pareto import dominates, frontier
from ..evaluation.scoring import beam_order
from .cegis import SearchConfig, evaluate_memory, repair_outcome
from .repairs import targeted_repairs, random_proposal, resource_proposal, Provenance
from .engine import software_commit


@dataclass(frozen=True)
class MalignantConfig:
    budget: int = 32
    seed: int = 0
    strategy: str = 'v03'
    target_dc: int = 3
    max_weight: int = 3
    max_combinations: int = 200000
    spectrum_work: int = 200000
    beam_width: int = 12
    initial_population: int = 6
    idles: bool = False
    equivalence: str = 'structural'
    protect_progress: bool = True
    dominant_order: bool = True
    coverage_priority: bool = True
    protected_slots: int = 4
    protection_age: int = 4
    compound_depth: int = 3
    representatives: int = 4
    option_limit: int = 16

    def __post_init__(self):
        if self.strategy not in ('random', 'resource', 'v02', 'v03', 'mixed'): raise ValueError('Unknown strategy')
        if self.equivalence not in ('raw', 'signature', 'structural'): raise ValueError('Unknown equivalence')
        if min(self.budget, self.beam_width, self.initial_population, self.compound_depth,
               self.representatives, self.option_limit) < 1: raise ValueError('Positive limits required')
        if not 0 <= self.protected_slots <= self.beam_width or self.protection_age < 0: raise ValueError('Invalid protection')
        SearchConfig(budget=self.budget, target_dc=self.target_dc, max_weight=self.max_weight,
                     max_combinations=self.max_combinations)
        if self.spectrum_work < 0: raise ValueError('Negative spectrum cap')


def count_at(record, weight, equivalence='structural'):
    layer = record['malignant_spectrum']['layers'].get(str(weight), {})
    return layer.get({'raw': 'raw_count', 'signature': 'signature_count', 'structural': 'class_count'}[equivalence]) if layer.get('complete') else None


def quality_key(record, equivalence='structural'):
    lower = record['bounds']['lower_bound']
    counts = [count_at(record, w, equivalence) for w in range(lower, max(map(int, record['malignant_spectrum']['layers']))+1)]
    # Unknown is not zero, and cannot rank ahead of a measured finite count.
    return (-lower, tuple((1, 0) if n is None else (0, n) for n in counts))


def malignant_dominates(a, b, equivalence='structural'):
    if a['bounds']['lower_bound'] < b['bounds']['lower_bound']: return False
    weight = b['bounds']['lower_bound']; ac = count_at(a, weight, equivalence); bc = count_at(b, weight, equivalence)
    if a['bounds']['lower_bound'] > weight: ac = 0
    if ac is None or bc is None:
        if a['bounds']['lower_bound'] == weight: return False
    elif ac > bc: return False
    metrics = ('Q', 'D', 'QD', 'two_q_gates')
    return all(a['resources'][m] <= b['resources'][m] for m in metrics) and (
        a['bounds']['lower_bound'] > weight or (ac is not None and bc is not None and ac < bc)
        or any(a['resources'][m] < b['resources'][m] for m in metrics))


def select_beam(pool, step, config, modern=True):
    by_id = {}
    for r in pool: by_id[r['architecture_id']] = r
    records = list(by_id.values())
    if modern:
        front = [r for r in records if not any(malignant_dominates(s, r, config.equivalence) for s in records if s is not r)]
        key = lambda r: (quality_key(r, config.equivalence), r['resources']['QD'], r['architecture_id'])
    else:
        front = frontier(records)
        key = beam_order
    protected = []
    if modern and config.protect_progress:
        protected = sorted([r for r in records if r.get('partial_progress') and
            step-r['evaluation_index'] <= config.protection_age and
            r['neutral_depth'] < config.compound_depth], key=key)[:config.protected_slots]
    beam = protected+ [r for r in sorted(front, key=key) if r not in protected][:config.beam_width-len(protected)]
    chosen = {r['evaluation_index'] for r in beam}; fids = {r['evaluation_index'] for r in front}
    reasons = [{'evaluation_node': r['evaluation_index'], 'architecture_id': r['architecture_id'],
                'decision': 'PROTECTED_PARTIAL_PROGRESS' if r in protected else 'PARETO_BEAM' if r['evaluation_index'] in chosen
                else 'BEAM_CAP' if r['evaluation_index'] in fids else 'DOMINATED',
                'protection_expired': bool(r.get('partial_progress') and step-r['evaluation_index'] > config.protection_age)} for r in records]
    return beam, front, reasons


def diverse_classes(classes, limit, dominant=True, recurrence=None):
    recurrence = recurrence or {}; selected = []; covered = set()
    def features(c):
        return {('check', m[1]) for m in c['mechanisms']} | {('round', m[0]) for m in c['mechanisms']} | {
            ('hook', tuple(c['hook_support'])), ('logical', c['logical_effect']), ('boundary', c.get('boundary_family')),
            *[('failure', f) for f in c.get('failure_classes', [])]}
    remaining = list(classes)
    while remaining and len(selected) < limit:
        if dominant:
            c = min(remaining, key=lambda x: (x['weight'], x.get('repairability') == 'UNSUPPORTED_REPAIR_CLASS',
                -len(features(x)-covered), -x['multiplicity'], -recurrence.get(x['id'], 0),
                -len(x['hook_support']), x['id']))
        else: c = remaining[0]
        selected.append(c); covered |= features(c); remaining.remove(c)
    return selected


def greedy_coverage(options, memory=None, enabled=True):
    """Expected coverage only; duplicated proposed architectures unify targets.

    Success memory is Laplace-smoothed and run-local. It breaks ties after
    cost-controlled uncovered-class coverage; no code-specific lookup is used.
    """
    memory = memory or {}; remaining = list(options); output = []; covered = set()
    while remaining:
        def rank(o):
            success, total = memory.get((o['provenance'].failure_class, o['provenance'].repair_operator), (0, 0))
            return (-len(set(o['covers'])-covered)/(1+o['estimated_added_cost']),
                    -(success+1)/(total+2), o['candidate'].id)
        choice = min(remaining, key=rank) if enabled else remaining[0]
        output.append(choice); covered.update(choice['covers']); remaining.remove(choice)
    return output


def repair_options(candidate, record, circuit, ss, config, rng, recurrence, operator_memory):
    spectrum = record['malignant_spectrum']; classes = []
    for cls in spectrum['classes']:
        w = representative_witness(circuit, ss, cls)
        family, support = boundary_class(w)
        # Cheap failure family first; detailed analysis only for chosen classes.
        hooks = bool(cls['hook_support'])
        classes.append({**cls, 'multiplicity': spectrum['layers'][str(cls['weight'])]['multiplicities'][cls['id']],
            'boundary_family': family, 'repairability': support,
            'failure_classes': ['BOUNDARY_READOUT_FAILURE'] if family == 'BOUNDARY_READOUT_FAILURE' else ['HOOK' if hooks else 'OTHER']})
    selected = diverse_classes(classes, config.representatives, config.dominant_order, recurrence)
    merged = {}; unsupported = []
    for cls in selected:
        w = representative_witness(circuit, ss, cls)
        if not verify_witness(circuit, w)['verified']: raise ArithmeticError('Representative failed replay')
        if cls['repairability'] == 'UNSUPPORTED_REPAIR_CLASS': unsupported.append(cls['id']); continue
        a = analyze(circuit, w, ss)
        offers = targeted_repairs(candidate, a, rng)
        if cls['boundary_family'] == 'BOUNDARY_READOUT_FAILURE' and candidate.terminal_repetitions < 1:
            offers.insert(0, (replace(candidate, terminal_repetitions=1), Provenance('COUNTEREXAMPLE_GUIDED', candidate.id,
                a.counterexample_id, 'BOUNDARY_READOUT_FAILURE', 'noisy_terminal_verification_round')))
        for child, prov in offers:
            cost = max(0, sum(map(len, child.flag_intervals))-sum(map(len, candidate.flag_intervals))) + max(0, child.terminal_repetitions-candidate.terminal_repetitions)
            option = merged.setdefault(child.id, {'candidate': child, 'provenance': prov,
                'source_class': cls['id'], 'source_witness': w, 'covers': [], 'estimated_added_cost': cost})
            option['covers'].append(cls['id'])
    ordered = greedy_coverage(list(merged.values()), operator_memory, config.coverage_priority)[:config.option_limit]
    return ordered, {'selected_classes': [c['id'] for c in selected], 'unsupported_classes': unsupported,
        'expected_coverage': [{'candidate_id': o['candidate'].id, 'class_ids': o['covers'], 'estimated_added_cost': o['estimated_added_cost']} for o in ordered]}


def classify_repair(parent, child, source_eliminated):
    delta = spectrum_delta(parent['malignant_spectrum'], child['malignant_spectrum'])
    weight = parent['bounds']['lower_bound']; d = delta.get(str(weight))
    pids = {c['id'] for c in parent['malignant_spectrum']['classes'] if c['weight'] == weight}
    cids = {c['id'] for c in child['malignant_spectrum']['classes'] if c['weight'] == weight}
    removed, added = pids-cids, cids-pids
    # Class turnover is mechanism-key disappearance, not proof of successful
    # transport. New alternatives and net regressions are reported separately.
    if child['bounds']['lower_bound'] < parent['bounds']['lower_bound'] or (d is not None and d > 0): category = 'REGRESSION'
    elif d is not None and d < 0: category = 'MULTI_CLASS_IMPROVEMENT' if len(removed) > 1 else 'CLASS_ELIMINATION'
    elif source_eliminated: category = 'SOURCE_ONLY'
    else: category = 'NEUTRAL'
    return {'category': category, 'delta_M': delta, 'removed_class_ids': sorted(removed), 'new_class_ids': sorted(added),
            'counts_comparable': d is not None, 'source_witness_eliminated': source_eliminated,
            'net_minimum_class_reduction': -d if d is not None else None}


def whole_class_result(statuses, unresolved_members, complete):
    return all(statuses) if complete and statuses and not unresolved_members else None


def bounded_compound(parent, child, config):
    same = child['bounds']['lower_bound'] == parent['bounds']['lower_bound']
    reduction = count_at(parent, parent['bounds']['lower_bound'], config.equivalence)
    after = count_at(child, parent['bounds']['lower_bound'], config.equivalence)
    useful = same and reduction is not None and after is not None and after < reduction
    depth = parent.get('neutral_depth', 0)+1 if useful else 0
    return useful and depth < config.compound_depth, depth


def run_malignant_search(code, memory=MemoryConfig(), config=MalignantConfig()):
    started = time.perf_counter(); rng = random.Random(config.seed)
    initial = list(generate(code, min(config.initial_population, config.budget), config.seed))
    records = []; cache = {}; circuits = {}; sigcache = {}; membercache = {}; beam = []; queues = {}
    recurrence = defaultdict(int); operator_memory = {}; selection = []; options_log = []; all_front = []; transfer_cache = {}
    modern = config.strategy in ('v03', 'mixed')
    baseconfig = SearchConfig(budget=config.budget, seed=config.seed, max_weight=config.max_weight,
        target_dc=config.target_dc, max_combinations=config.max_combinations, decoder_weight=0, idles=config.idles)
    for step in range(1, config.budget+1):
        parent = None; option = None; source = None
        if step <= len(initial):
            candidate = initial[step-1]; prov = Provenance('RANDOM', repair_operator='initial_population')
        else:
            protected = [r for r in beam if r.get('partial_progress') and step-r['evaluation_index'] <= config.protection_age and r['neutral_depth'] < config.compound_depth]
            parent = min(protected, key=lambda r: (quality_key(r, config.equivalence), r['evaluation_index'])) if modern and config.protect_progress and protected else rng.choice(beam)
            candidate = Candidate.from_dict(parent['candidate']); choice = config.strategy
            if choice == 'mixed': choice = 'random' if rng.randrange(3) == 0 else 'v03'
            if choice in ('v02', 'v03') and parent['bounds'].get('witness'):
                node = parent['architecture_id']
                if node not in queues:
                    if choice == 'v03' and parent.get('neutral_depth', 0) < config.compound_depth:
                        queues[node], log = repair_options(candidate, parent, circuits[candidate.id], sigcache[candidate.id], config, rng, recurrence, operator_memory)
                        options_log.append({'parent_node': parent['evaluation_index'], **log})
                    elif choice == 'v02':
                        a = analyze(circuits[candidate.id], parent['bounds']['witness'], sigcache[candidate.id])
                        queues[node] = [{'candidate': c, 'provenance': p, 'source_witness': parent['bounds']['witness'], 'source_class': None, 'covers': []} for c,p in targeted_repairs(candidate, a, rng)]
                    else: queues[node] = []
                if queues[node]:
                    option = queues[node].pop(0); candidate = option['candidate']; prov = option['provenance']; source = option['source_witness']
                else: candidate, prov = random_proposal(candidate, rng)
            elif choice == 'resource': candidate, prov = resource_proposal(candidate, rng)
            else: candidate, prov = random_proposal(candidate, rng)
            # Same boundary library available to all random/exploration arms.
            if prov.kind == 'RANDOM' and rng.randrange(12) == 0:
                candidate = replace(candidate, terminal_repetitions=1-candidate.terminal_repetitions)
                prov = Provenance('RANDOM', parent['architecture_id'], repair_operator='toggle_noisy_terminal_round')
        cached = candidate.id in cache
        if not cached:
            record, circuit = evaluate_memory(code, candidate, memory, baseconfig, transfer_cache)
            ss = transfer_cache[record['circuit_hash']]
            before = time.perf_counter(); spectrum, members = malignant_spectrum(circuit, ss, config.max_weight, config.spectrum_work)
            record['malignant_spectrum'] = spectrum; record['spectrum_seconds'] = time.perf_counter()-before
            record['runtime_seconds'] += record['spectrum_seconds']
            cache[candidate.id] = record; circuits[candidate.id] = circuit; sigcache[candidate.id] = ss; membercache[candidate.id] = members
        record = {**cache[candidate.id], 'evaluation_index': step, 'cached_evaluation': cached,
            'provenance': prov.to_dict(), 'parent_node': parent['evaluation_index'] if parent else None,
            'source_class_id': option['source_class'] if option else None,
            'source_witness': source, 'expected_covered_classes': option['covers'] if option else [],
            'elapsed_seconds': time.perf_counter()-started, 'partial_progress': False, 'neutral_depth': 0,
            'repair_chain_length': parent.get('repair_chain_length', 0)+1 if parent and prov.kind == 'COUNTEREXAMPLE_GUIDED' else 0}
        if parent:
            record['spectrum_before'] = parent['malignant_spectrum']['layers']
            record['resource_delta'] = {m: record['resources'][m]-parent['resources'][m] for m in ('Q','D','QD','two_q_gates')}
            record['dc_delta'] = record['bounds']['lower_bound']-parent['bounds']['lower_bound']
            if record['dc_delta'] > 0:
                from ..faults.exclusion import verify_exclusion
                certificate = cache[candidate.id].get('independent_exclusion')
                if certificate is None:
                    certificate = verify_exclusion(circuits[candidate.id], record['bounds']['lower_bound']-1, config.idles)
                    cache[candidate.id]['independent_exclusion'] = certificate
                if not certificate['verified']: raise ArithmeticError('Exhaustive independent exclusion failed')
                record['independent_exclusion'] = certificate
            eliminated = None; whole = None; unresolved_members = 0
            if source:
                mapped, reason = transport_witness(circuits[parent['architecture_id']], circuits[candidate.id], source)
                if mapped is not None:
                    actual = replay(circuits[candidate.id], mapped); eliminated = bool(actual['detector_outcomes'] or not actual['logical_coset'])
                record['source_transport_reason'] = reason
                cid = record['source_class_id']
                if cid:
                    statuses = []
                    for indices in membercache[parent['architecture_id']].get(cid, []):
                        from ..faults.search import witness
                        member = witness(circuits[parent['architecture_id']], [sigcache[parent['architecture_id']][i] for i in indices]).to_dict()
                        transported, _ = transport_witness(circuits[parent['architecture_id']], circuits[candidate.id], member)
                        if transported is None: unresolved_members += 1; continue
                        effect = replay(circuits[candidate.id], transported)
                        statuses.append(bool(effect['detector_outcomes'] or not effect['logical_coset']))
                    complete = parent['malignant_spectrum']['layers'][str(source['fault_count'])]['complete']
                    whole = whole_class_result(statuses, unresolved_members, complete)
            outcome = classify_repair(parent, record, eliminated)
            outcome.update(transported_source_class_eliminated=whole, unresolved_source_class_members=unresolved_members)
            record['repair_outcome_v03'] = outcome
            record['partial_progress'], record['neutral_depth'] = bounded_compound(parent, record, config)
            d = outcome['net_minimum_class_reduction']; gained = record['dc_delta']
            record['QD_per_class_eliminated'] = record['resource_delta']['QD']/d if d and d > 0 else None
            record['QD_per_dc_tier_gained'] = record['resource_delta']['QD']/gained if gained > 0 else None
            if prov.kind == 'COUNTEREXAMPLE_GUIDED':
                key = (prov.failure_class, prov.repair_operator); success, total = operator_memory.get(key, (0, 0))
                operator_memory[key] = (success+int(outcome['category'] in ('CLASS_ELIMINATION','MULTI_CLASS_IMPROVEMENT')), total+1)
        for cls in record['malignant_spectrum']['classes']: recurrence[cls['id']] += 1
        records.append(record)
        beam, all_front, decisions = select_beam(records, step, config, modern)
        selection.append({'evaluation_index': step, 'decisions': decisions})
    tiers = {}; chains = []
    for r in records:
        for tier in range(1, r['bounds']['lower_bound']+1): tiers.setdefault(str(tier), r['evaluation_index'])
        if r.get('dc_delta', 0) > 0:
            chain = [r]; p = r['parent_node']
            while p:
                ancestor = records[p-1]; chain.append(ancestor); p = ancestor['parent_node']
            chain.reverse()
            chains.append({'gain_node': r['evaluation_index'], 'nodes': [a['evaluation_index'] for a in chain],
                'architecture_ids': [a['architecture_id'] for a in chain],
                'spectra': [a['malignant_spectrum']['layers'] for a in chain],
                'operators': [a['provenance']['repair_operator'] for a in chain],
                'targeted_classes': [a['source_class_id'] for a in chain],
                'resource_delta': {m: r['resources'][m]-chain[0]['resources'][m] for m in ('Q','D','QD','two_q_gates')},
                'neutral_progress_steps': sum(a['partial_progress'] for a in chain),
                'guided_steps': sum(a['provenance']['kind']=='COUNTEREXAMPLE_GUIDED' for a in chain)})
    best_dc = max(r['bounds']['lower_bound'] for r in records)
    best = min([r for r in records if r['bounds']['lower_bound']==best_dc], key=lambda r: (quality_key(r, config.equivalence), r['resources']['QD']))
    tier_resources = {str(t): {m: min(r['resources'][m] for r in records if r['bounds']['lower_bound'] >= t) for m in ('Q','D','QD','two_q_gates')} for t in range(1, best_dc+1)}
    return json_native({'schema_version': '0.3', 'software_version': '0.3.0', 'software_git_commit': software_commit(),
        'code': code.to_dict(), 'code_input_hash': code.input_hash, 'configuration': asdict(config),
        'memory_configuration': asdict(memory), 'initial_population_ids': [c.id for c in initial],
        'evaluation_slots': len(records), 'unique_candidates_evaluated': len(cache), 'mutation_count': len(records)-len(initial),
        'summary': {'best_dc_lower_bound': best_dc, 'minimum_witness_weight': best['bounds']['upper_bound'],
            'malignant_spectrum': best['malignant_spectrum']['layers'], 'best_resources_by_tier': tier_resources,
            'target_reached': str(config.target_dc) in tiers, 'evaluations_to_target': tiers.get(str(config.target_dc)),
            'maximum_repair_chain_length': max(r['repair_chain_length'] for r in records),
            'successful_compositions': sum(c['neutral_progress_steps'] > 0 and c['guided_steps'] > 1 for c in chains)},
        'frontier': [r['evaluation_index'] for r in all_front], 'records': records, 'selection_history': selection,
        'repair_options': options_log, 'distance_gain_chains': chains,
        'operator_memory': [{'failure_class': k[0], 'operator': k[1], 'successes': v[0], 'attempts': v[1]} for k,v in sorted(operator_memory.items())],
        'runtime_seconds': time.perf_counter()-started})
