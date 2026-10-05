"""Guarded public experiment runner; existing freeze and raw evidence retained."""
import argparse
import json,hashlib
from v04_development import OUT,freeze,run_primary,run_secondary,audit,assert_frozen

def main():
    p=argparse.ArgumentParser(); p.add_argument('action',choices=('freeze','primary','secondary','audit','verify'))
    action=p.parse_args().action
    if action=='freeze':
        if (OUT/'experiment_freeze.json').exists():
            raise SystemExit('Existing experiment freeze retained; use verify, not freeze, to check it.')
        return freeze()
    if action=='verify':
        assert_frozen()
        from v04_development import ROOT
        for name,h in json.loads((OUT/'v01_preservation.json').read_text())['hashes'].items():
            assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==h,name
        return
    {'primary':run_primary,'secondary':run_secondary,'audit':audit}[action]()

if __name__=='__main__': main()
