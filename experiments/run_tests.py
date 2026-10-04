"""Run tests and save machine-readable verification status."""
import json
from pathlib import Path
import unittest

root = Path(__file__).resolve().parents[1]
suite = unittest.defaultTestLoader.discover(str(root / 'tests'))
result = unittest.TextTestRunner(verbosity=2).run(suite)
summary = {
    'tests_run': result.testsRun,
    'passed': result.testsRun - len(result.failures) - len(result.errors) - len(result.skipped),
    'failures': [(str(test), text) for test, text in result.failures],
    'errors': [(str(test), text) for test, text in result.errors],
    'skipped': [(str(test), reason) for test, reason in result.skipped],
    'successful': result.wasSuccessful(),
}
(root / 'results').mkdir(exist_ok=True)
(root / 'results' / 'verification.json').write_text(json.dumps(summary, indent=2) + '\n')
raise SystemExit(0 if result.wasSuccessful() else 1)
