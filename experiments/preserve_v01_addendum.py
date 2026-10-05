"""Prove V0.1 root-level results against the immutable pre-V0.4 archive."""
from pathlib import Path
import hashlib,json,zipfile
ROOT=Path(__file__).resolve().parents[1]
archive=ROOT/'dist/ftqec-development-suite-2.zip'
expected='d5bbad5b3860bdc52013b6d5e50344b02fa4b402f2b32414483c07a01368a3f0'
assert hashlib.sha256(archive.read_bytes()).hexdigest()==expected
hashes={}
with zipfile.ZipFile(archive) as z:
    for name in z.namelist():
        if name.startswith('results/development/') or (name.startswith('results/') and name.count('/')==1):
            if name.endswith('/'): continue
            h=hashlib.sha256(z.read(name)).hexdigest()
            assert (ROOT/name).is_file() and hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==h,name
            hashes[name]=h
out=ROOT/'results/v0.4/v01_preservation.json'
assert not out.exists(),'Refusing to replace existing preservation evidence'
out.write_text(json.dumps({'baseline_commit':'fd29e51d17bfd1e8855fefe257bf22b132525dba',
    'baseline_archive_sha256':expected,'scope':'V0.1 root-level and development results, verified against pre-V0.4 archive',
    'verified':True,'hashes':hashes},indent=2)+'\n')
print('V0.1 archived baseline matches',len(hashes),'unchanged current files')
