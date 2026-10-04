"""Execute the complete installed pytest suite and save machine-readable status."""
import json
import argparse
from pathlib import Path
import subprocess
import sys
import xml.etree.ElementTree as ET

root = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser()
parser.add_argument('--results-dir', default='results/v0.3')
args = parser.parse_args()
out = root / args.results_dir
out.mkdir(parents=True, exist_ok=True)
report = out / 'junit.xml'
command = [sys.executable, '-m', 'pytest', '-q', '--basetemp', str(root / '.pytest-tmp/v03-final'),
           '--junitxml', str(report)]
result = subprocess.run(command, cwd=root)
suites = ET.parse(report).getroot().iter('testsuite') if report.exists() else []
counts = {name: 0 for name in ('tests', 'failures', 'errors', 'skipped')}
for suite in suites:
    for name in counts: counts[name] += int(suite.get(name, '0'))
summary = {'tests_run': counts['tests'],
           'passed': counts['tests']-counts['failures']-counts['errors']-counts['skipped'],
           'failures': counts['failures'], 'errors': counts['errors'], 'skipped': counts['skipped'],
           'successful': result.returncode == 0 and counts['skipped'] == 0,
           'pytest_exit_code': result.returncode}
(out / 'verification.json').write_text(json.dumps(summary, indent=2) + '\n')
raise SystemExit(0 if summary['successful'] else 1)
