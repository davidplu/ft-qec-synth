"""Guarded public experiment runner; existing freeze and raw evidence retained."""
import argparse
from v04_development import OUT,freeze,run_primary,run_secondary,audit,assert_frozen

def main():
    p=argparse.ArgumentParser(); p.add_argument('action',choices=('freeze','primary','secondary','audit','verify'))
    action=p.parse_args().action
    if action=='freeze':
        if (OUT/'experiment_freeze.json').exists():
            raise SystemExit('Existing experiment freeze retained; use verify, not freeze, to check it.')
        return freeze()
    {'primary':run_primary,'secondary':run_secondary,'audit':audit,'verify':assert_frozen}[action]()

if __name__=='__main__': main()
