"""Budget-matched search strategies for repeated-memory architecture experiments."""
from dataclasses import dataclass, asdict
from hashlib import sha256
import json
import random
import time
from ..architectures.generators import generate
from ..architectures.candidate import Candidate
from ..circuits.memory import MemoryConfig, build_memory
from ..evaluation.resources import resources
from ..evaluation.pareto import frontier, dominates
from ..evaluation.scoring import beam_order
from ..faults.signatures import signatures
from ..faults.search import search_faults
from ..faults.verification import verify_witness, replay
from ..faults.analysis import analyze, transport_witness
from ..decoding.minimum_weight import BoundedMinimumWeightDecoder, decoder_failures
from .repairs import Provenance, targeted_repairs, random_proposal, resource_proposal
from .engine import software_commit
from ..serialization import json_native


@dataclass(frozen=True)
class SearchConfig:
    budget: int = 32
    seed: int = 0
    strategy: str = 'cegis'
    target_dc: int = 3
    max_weight: int = 3
    max_combinations: int = 200000
    beam_width: int = 12
    initial_population: int = 6
    idles: bool = False
    decoder_weight: int = 1
    resource_limits: tuple = ()

    def __post_init__(self):
        if self.budget < 1 or self.beam_width < 1 or self.initial_population < 1:
            raise ValueError('Positive search limits required')
        if self.strategy not in ('random', 'resource', 'cegis', 'mixed'):
            raise ValueError('Unknown strategy')
        if not 1 <= self.max_weight <= 6 or not 1 <= self.target_dc <= self.max_weight+1:
            raise ValueError('Invalid distance/search weight')
        if self.max_combinations < 0 or self.decoder_weight not in (0, 1, 2):
            raise ValueError('Invalid work/decoder limits')


def evaluate_memory(code, candidate, memory, config):
    started = time.perf_counter()
    circuit = build_memory(code, candidate, memory)
    metrics = resources(circuit)
    rec = {'architecture_id': candidate.id, 'candidate': candidate.to_dict(), 'resources': metrics,
           'circuit_hash': sha256(json.dumps(circuit.to_dict(), sort_keys=True).encode()).hexdigest(),
           'bounds': {'status': 'UNRESOLVED', 'lower_bound': 1, 'upper_bound': None, 'excluded_through': 0},
           'rejection': None, 'stage': 'A'}
    if any(metrics[name] > limit for name, limit in config.resource_limits):
        rec['rejection'] = 'A_resource_limit'
        rec['runtime_seconds'] = time.perf_counter()-started
        return rec, circuit
    before = time.perf_counter()
    ss = signatures(circuit, config.idles)
    rec['signature_seconds'] = time.perf_counter()-before
    before = time.perf_counter()
    bounds = search_faults(circuit, ss, config.max_weight, config.max_combinations)
    rec['bounds'] = bounds
    rec['fault_search_seconds'] = time.perf_counter()-before
    rec['stage'] = 'B' if bounds['upper_bound'] == 1 else 'C' if bounds['upper_bound'] == 2 else 'D'
    if bounds['witness']:
        verification = verify_witness(circuit.to_dict(), bounds['witness'])
        if not verification['verified']: raise ArithmeticError('Independent witness verification failed')
        rec['witness_verification'] = {'verified': True, 'path': 'boolean_array_simultaneous_replay'}
        rec['counterexample_analysis'] = analyze(circuit, bounds['witness'], ss).to_dict()
    if bounds['lower_bound'] < config.target_dc:
        rec['rejection'] = 'logical_witness_below_target' if bounds['upper_bound'] else 'incomplete_distance_screen'
    if config.decoder_weight:
        decoder = BoundedMinimumWeightDecoder().fit(ss, config.decoder_weight, config.max_combinations)
        rec['decoder'] = {'name': 'bounded_minimum_weight_detector_logical_recovery',
                          'training_completed_through': decoder.completed_through,
                          **decoder_failures(ss, decoder, config.decoder_weight, config.max_combinations)}
    rec['runtime_seconds'] = time.perf_counter()-started
    return rec, circuit


def repair_outcome(parent, child, parent_circuit, child_circuit):
    w = parent['bounds']['witness']
    mapped, reason = transport_witness(parent_circuit, child_circuit, w)
    eliminated = None
    if mapped is not None:
        result = replay(child_circuit.to_dict(), mapped)
        eliminated = bool(result['detector_outcomes'] or not result['logical_coset'])
    pb, cb = parent['bounds'], child['bounds']
    raised = cb['lower_bound'] > pb['upper_bound']
    preserved = pb['status'] == cb['status'] == 'EXACT' and pb['upper_bound'] == cb['upper_bound']
    improved_resources = preserved and dominates(child, parent, include_distance=False)
    return {'eliminates_source_witness': eliminated, 'transport_reason': reason,
            'raises_minimum_witness_weight': raised,
            'improves_distance_lower_bound': cb['lower_bound'] > pb['lower_bound'],
            'preserves_exact_distance_improves_resources': improved_resources,
            'equal_or_worse_witness': cb['upper_bound'] is not None and cb['upper_bound'] <= pb['upper_bound'],
            'fails_or_equal_or_worse_without_quality_gain': not (raised or cb['lower_bound'] > pb['lower_bound'] or improved_resources),
            'repair_success': raised or cb['lower_bound'] > pb['lower_bound'] or improved_resources}


def resource_frontier(records, target_dc):
    eligible = [r for r in records if r['bounds']['lower_bound'] >= target_dc and r['rejection'] is None]
    selected = frontier(eligible)
    return [a for a in selected if not any(dominates(b, a, include_distance=False) for b in selected if b is not a)]


def run_search(code, memory=MemoryConfig(), config=SearchConfig()):
    started = time.perf_counter(); rng = random.Random(config.seed)
    initial = list(generate(code, min(config.initial_population, config.budget), config.seed))
    records = []; cache = {}; circuits = {}; beam = []; all_front = []; by_id = {}
    queues = {}; consumed = set(); proposals = []
    for step in range(config.budget):
        if step < len(initial):
            candidate = initial[step]; provenance = Provenance('RANDOM', repair_operator='initial_population')
        else:
            parent = rng.choice(beam)
            candidate = Candidate.from_dict(parent['candidate'])
            choice = config.strategy
            if choice == 'mixed': choice = rng.choice(('random', 'resource', 'cegis'))
            if choice == 'cegis' and parent['bounds'].get('witness'):
                from ..faults.analysis import CounterexampleAnalysis
                analysis = CounterexampleAnalysis(**parent['counterexample_analysis'])
                if parent['architecture_id'] not in queues:
                    queues[parent['architecture_id']] = targeted_repairs(candidate, analysis, rng)
                options = queues[parent['architecture_id']]
                if options:
                    candidate, provenance = options.pop(0)
                    consumed.add(analysis.counterexample_id)
                else: candidate, provenance = random_proposal(candidate, rng)
            elif choice == 'resource': candidate, provenance = resource_proposal(candidate, rng)
            else: candidate, provenance = random_proposal(candidate, rng)
        cached = candidate.id in cache
        if cached:
            # Duplicate proposals consume an evaluation slot in every strategy.
            record = {**cache[candidate.id], 'runtime_seconds': 0.0}
            circuit = circuits[candidate.id]
        else:
            record, circuit = evaluate_memory(code, candidate, memory, config)
            cache[candidate.id] = record; circuits[candidate.id] = circuit
        record = {**record, 'evaluation_index': step+1, 'cached_evaluation': cached,
                  'provenance': provenance.to_dict(), 'elapsed_seconds': time.perf_counter()-started}
        if provenance.kind == 'COUNTEREXAMPLE_GUIDED':
            parent = by_id[provenance.parent_id]
            record['repair_outcome'] = repair_outcome(parent, record, circuits[provenance.parent_id], circuit)
        records.append(record); by_id[candidate.id] = record
        proposals.append({'evaluation_index': step+1, 'architecture_id': candidate.id,
                          'cached': cached, **provenance.to_dict()})
        all_front = frontier(all_front+[record])
        beam = sorted(all_front, key=beam_order)[:config.beam_width]
    tiers = {}
    for r in records:
        for tier in range(1, r['bounds']['lower_bound']+1):
            tiers.setdefault(str(tier), {'evaluation': r['evaluation_index'], 'seconds': r['elapsed_seconds']})
    conditioned = resource_frontier(records, config.target_dc)
    reached = tiers.get(str(config.target_dc))
    quality = max(r['bounds']['lower_bound'] for r in records)
    best = [r for r in records if r['bounds']['lower_bound'] == quality]
    repairs = [r for r in records if 'repair_outcome' in r]
    transportable = [r for r in repairs if r['repair_outcome']['eliminates_source_witness'] is not None]
    summary = {'best_dc_lower_bound': quality,
               'minimum_witness_weight_at_best_dc': min((r['bounds']['upper_bound'] for r in best if r['bounds']['upper_bound']),default=None),
               'minimum_witness_weight': min((r['bounds']['upper_bound'] for r in records if r['bounds']['upper_bound']), default=None),
               'best_resources_at_best_dc': {m: min(r['resources'][m] for r in best) for m in ('Q','D','QD','two_q_gates')},
               'first_dc_tiers': tiers, 'evaluations_to_target_dc': reached['evaluation'] if reached else None,
               'time_to_target_dc': reached['seconds'] if reached else None,
               'best_QD_at_target_dc': min((r['resources']['QD'] for r in conditioned), default=None),
               'target_reached': bool(reached), 'counterexamples_consumed': len(consumed),
               'repairs_evaluated': len(repairs),
               'repair_success_rate': sum(r['repair_outcome']['repair_success'] for r in repairs)/len(repairs) if repairs else None,
               'witness_elimination_rate': sum(r['repair_outcome']['eliminates_source_witness'] for r in transportable)/len(transportable) if transportable else None}
    return json_native({'schema_version': '0.2', 'software_version': '0.2.0', 'software_git_commit': software_commit(),
            'code': code.to_dict(), 'code_input_hash': code.input_hash, 'seed': config.seed,
            'configuration': asdict(config), 'memory_configuration': asdict(memory),
            'fault_model': 'repeated noisy extraction; ideal encoded input; physical product-basis final data readout',
            'initial_population_ids': [c.id for c in initial], 'evaluation_slots': len(records),
            'unique_candidates_evaluated': len(cache), 'candidates_evaluated': len(cache), 'mutation_count': len(records)-len(initial),
            'summary': summary, 'frontier': conditioned, 'exploratory_frontier': all_front,
            'records': records, 'proposals': proposals, 'runtime_seconds': time.perf_counter()-started})
