import json
from pathlib import Path
import jsonschema
from ftqec.architectures.generators import generate
from ftqec.circuits.extraction import build
from ftqec.codes.stabilizer import StabilizerCode


def test_native_objects_match_schema_without_json_roundtrip():
    root = Path(__file__).resolve().parents[1]
    schema = json.loads((root / 'docs/schemas/result.schema.json').read_text())
    code = StabilizerCode.from_dict({'generators': ['XXXX', 'ZZZZ']})
    candidate = next(generate(code, 1))
    native = candidate.to_dict()
    assert isinstance(native['orders'], list)
    assert isinstance(native['orders'][0], list)
    assert isinstance(native['flag_intervals'], list)
    jsonschema.validate(native, {'$defs': schema['$defs'], '$ref': '#/$defs/candidate'})
    circuit_schema = json.loads((root / 'docs/schemas/circuit.schema.json').read_text())
    jsonschema.validate(build(code, candidate).to_dict(), circuit_schema)
