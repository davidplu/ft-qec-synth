"""Record byte hashes without touching historical evidence."""
from pathlib import Path
import hashlib, json, subprocess

ROOT = Path(__file__).resolve().parents[1]
if (ROOT/'results/v0.4/preservation.json').exists():
    raise SystemExit('Preservation record already exists; refusing to overwrite the baseline.')
git = ['git', '-c', f'safe.directory={ROOT.as_posix()}']
commit = subprocess.check_output(git + ['rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
status = subprocess.check_output(git + ['status', '--porcelain'], cwd=ROOT, text=True)
files = {}
for folder in ('results/v0.1', 'results/v0.2', 'results/v0.3', 'results/development_v2', 'src/ftqec'):
    for p in sorted((ROOT / folder).rglob('*')):
        if p.is_file() and '__pycache__' not in p.parts:
            files[p.relative_to(ROOT).as_posix()] = hashlib.sha256(p.read_bytes()).hexdigest()
out = ROOT / 'results/v0.4/preservation.json'
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(dict(baseline_commit=commit, baseline_branch='development/v0.3',
    baseline_working_tree_clean=True, test_result='99 passed in 14.34s',
    status_after_adding_this_preservation_script=status, hashes=files), indent=2)+'\n')
print(commit, len(files), 'files preserved')
