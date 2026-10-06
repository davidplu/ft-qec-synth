"""Hash final evidence and scan prospective commit content for credential patterns."""
from pathlib import Path
from hashlib import sha256
import gzip,json,re,xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'results/v0.5'
def main():
    suites=ET.parse(OUT/'final_tests.xml').getroot().iter('testsuite')
    counts={k:0 for k in ('tests','failures','errors','skipped')};seconds=0
    for s in suites:
        for k in counts:counts[k]+=int(s.get(k,0))
        seconds+=float(s.get('time',0))
    passed=counts['tests']-sum(counts[k] for k in ('failures','errors','skipped'))
    result=dict(**counts,passed=passed,successful=passed==counts['tests'] and passed>0,seconds=seconds)
    (OUT/'test_verification.json').write_text(json.dumps(result,indent=2)+'\n')
    paths=[]
    for directory in ('src/ftqec/certification_v5','benchmarks/certification_v5','results/v0.5'):
        paths.extend(p for p in (ROOT/directory).rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.pyc')
    paths+=list((ROOT/'experiments').glob('*v05*.py'))+list((ROOT/'docs').glob('V0_5*.md'))
    paths+=[ROOT/'tests/test_certification_v5.py',ROOT/'README.md',ROOT/'pyproject.toml',ROOT/'.gitattributes']
    pattern=re.compile(rb'gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{30,}|sk-[A-Za-z0-9]{30,}|AKIA[A-Z0-9]{16}|-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----')
    for p in paths:
        data=p.read_bytes()
        if p.suffix=='.gz':data=gzip.decompress(data)
        if pattern.search(data):raise ValueError('Potential credential in '+str(p))
    manifest={p.relative_to(ROOT).as_posix():dict(sha256=sha256(p.read_bytes()).hexdigest(),bytes=p.stat().st_size)
              for p in paths if p.name not in ('artifact_manifest.json','artifact_review.json')}
    (OUT/'artifact_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    review=dict(credential_pattern_hits=0,files_scanned=len(paths),scan_scope='Known token/private-key patterns including decompressed raw JSON; not a proof of absence of every secret',
                total_bytes=sum(x['bytes'] for x in manifest.values()),largest_bytes=max(x['bytes'] for x in manifest.values()),
                excluded='Virtual environments, caches, wheel/build output, temporary smoke files and generated egg-info remain ignored',
                binary_model_reason='Small exported reproducible physical SAT models; raw generated experimental evidence intentionally retained')
    (OUT/'artifact_review.json').write_text(json.dumps(review,indent=2)+'\n')
    print(json.dumps(result));print(json.dumps(review))
if __name__=='__main__':main()
