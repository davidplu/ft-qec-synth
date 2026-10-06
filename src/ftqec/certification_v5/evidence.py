"""Verify serialized bounds without trusting stored verification flags."""
from ..faults.verification import verify_witness
from .projection import verify as verify_projection
from .artifacts import verify as verify_native

def verify(circuit,bounds):
    lower=bounds.get('lower_bound');upper=bounds.get('upper_bound');w=bounds.get('witness')
    if not isinstance(lower,int) or lower<1:return dict(verified=False,reason='invalid_lower_bound')
    if upper is not None:
        if not isinstance(upper,int) or upper<lower or not w:return dict(verified=False,reason='invalid_upper_bound')
        if w.get('fault_count')!=len(w.get('faults',[])) or upper!=w['fault_count']:
            return dict(verified=False,reason='witness_weight_mismatch')
        if not verify_witness(circuit.to_dict(),w)['verified']:return dict(verified=False,reason='witness_replay_failed')
    if bounds.get('status')=='EXACT' and upper!=lower:return dict(verified=False,reason='invalid_exact_status')
    cert=bounds.get('certificate',{});payload=cert.get('payload',{})
    if cert.get('algorithm_version')==payload.get('algorithm') and 'coordinate_masks' in payload:
        from hashlib import sha256
        from .exact import FAULT_MODEL
        if cert.get('fault_model_hash')!=sha256(FAULT_MODEL.encode()).hexdigest():
            return dict(verified=False,reason='fault_model_hash')
        for key in ('circuit_hash','fault_inventory_hash'):
            if cert.get(key)!=payload.get(key):return dict(verified=False,reason=key)
        result=verify_projection(circuit,payload)
        if lower>payload.get('lower_bound',0):return dict(verified=False,reason='projection_bound_overstatement')
        return result
    return verify_native(circuit,bounds)
