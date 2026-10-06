"""Certificate metadata validation and independently replayed exclusion claims."""
from hashlib import sha256
import json
from ..resource_synthesis.certification import fingerprint
from ..faults.signatures import enumerate_faults
from ..faults.verification import verify_witness
from ..faults.exclusion import verify_exclusion
from .exact import FAULT_MODEL,VERSION
from .independent import exclusion


def verify(circuit,bounds,state_limit=250000,work_limit=2000000):
    cert=bounds['certificate'];inventory=[f.to_dict() for f in enumerate_faults(circuit,False)]
    expected=dict(circuit_hash=fingerprint(circuit),fault_model_hash=sha256(FAULT_MODEL.encode()).hexdigest(),
                  fault_inventory_hash=sha256(json.dumps(inventory,sort_keys=True).encode()).hexdigest(),
                  algorithm_version=VERSION)
    for name,value in expected.items():
        if cert.get(name)!=value:return dict(verified=False,reason='metadata_mismatch',field=name)
    if bounds.get('witness') and not verify_witness(circuit.to_dict(),bounds['witness'])['verified']:
        return dict(verified=False,reason='witness_replay_failed')
    through=bounds['lower_bound']-1
    audit=verify_exclusion(circuit,through) if through<=3 else exclusion(circuit,through,state_limit,work_limit)
    return dict(verified=audit['verified'],exclusion=audit)
