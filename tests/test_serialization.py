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


def test_cli_utf8_input_preserves_name_and_input_hash(tmp_path):
    from ftqec.cli import main
    code={'name':'research \u7814\u7a76 \u00b5', 'generators':['ZZ']}
    source=tmp_path/'code.json'; result=tmp_path/'result.json'
    source.write_text(json.dumps(code,ensure_ascii=False),encoding='utf-8')
    main(['search',str(source),'--budget','1','--max-weight','1','--target-dc','2','-o',str(result)])
    saved=json.loads(result.read_text(encoding='utf-8'))
    assert saved['code']['name']==code['name']
    assert saved['code_input_hash']==StabilizerCode.from_dict(code).input_hash
