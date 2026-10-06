"""Exercise public entrypoints from the final wheel with isolated imports."""
from pathlib import Path
from hashlib import sha256
import json,subprocess,sys,zipfile
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'results/v0.5'
def main():
    wheel=ROOT/'dist/ftqec-0.5.0-py3-none-any.whl';tmp=ROOT/'.pytest-tmp/v05-wheel-smoke';tmp.mkdir(parents=True,exist_ok=True)
    source="""import sys,json
from pathlib import Path
sys.path.insert(0,sys.argv[1])
from ftqec.certification_v5.entrypoint import main
from ftqec.codes.stabilizer import StabilizerCode
from ftqec.architectures.generators import generate
from ftqec.resource_synthesis.design import Design
p=Path(sys.argv[2]);code=StabilizerCode.from_dict(dict(n=3,generators=['ZZI','IZZ']))
(p/'code.json').write_text(json.dumps(code.to_dict()))
(p/'design.json').write_text(json.dumps(Design(next(iter(generate(code,1,10)))).to_dict()))
main(['search',str(p/'code.json'),'-o',str(p/'search.json'),'--budget','1','--descent-evaluations','0','--final-audit-evaluations','0'])
main(['certify',str(p/'code.json'),'--design',str(p/'design.json'),'-o',str(p/'cert.json'),'--target-dc','3','--rounds','1'])
main(['verify-certificate',str(p/'cert.json'),'-o',str(p/'verified.json')])
assert json.loads((p/'verified.json').read_text())['verified']
assert json.loads((p/'cert.json').read_text())['independently_verified_target']
from ftqec.resource_synthesis.entrypoint import main as v04
from ftqec.cli import main as v03
print('Isolated wheel search, certify, certificate verification, historical imports passed')
"""
    result=subprocess.run([sys.executable,'-I','-c',source,str(wheel),str(tmp)],capture_output=True,text=True)
    if result.returncode:raise RuntimeError(result.stdout+result.stderr)
    with zipfile.ZipFile(wheel) as z:
        entrypoints=z.read('ftqec-0.5.0.dist-info/entry_points.txt').decode()
    out=dict(verified=True,wheel=wheel.name,sha256=sha256(wheel.read_bytes()).hexdigest(),bytes=wheel.stat().st_size,
        isolated_python=True,stdout=result.stdout,entrypoints=entrypoints)
    (OUT/'packaging_verification.json').write_text(json.dumps(out,indent=2)+'\n');print(result.stdout)
if __name__=='__main__':main()
