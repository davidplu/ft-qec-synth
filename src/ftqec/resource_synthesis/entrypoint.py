"""Public V0.4 CLI wiring conservative diagnostic labels into frozen search."""
from . import cli
from .audits import protection_audit
from .inventory import design_inventory
from ..codes.stabilizer import StabilizerCode
from pathlib import Path
import json,sys


def main(argv=None):
    # Dependency injection at the process entry point preserves the archived
    # experiment CLI and search source bytes. No search behavior is changed.
    original=cli.protection_audit
    cli.protection_audit=protection_audit
    try:
        args=list(sys.argv[1:] if argv is None else argv)
        result=cli.main(args)
        if args and args[0]=='search':
            output=next((arg.split('=',1)[1] for arg in args if arg.startswith('--output=')),None)
            if output is None:
                pos=next(i for i,a in enumerate(args) if a in ('-o','--output')); output=args[pos+1]
            path=Path(output); data=json.loads(path.read_text())
            data['design_inventory']=design_inventory(StabilizerCode.from_dict(data['code']),data['records'])
            data['repair_statistics_scope']='run-local parent witness representative outcomes; full-class diagnostic audit is separate'
            path.write_text(json.dumps(data,indent=2,allow_nan=False)+'\n')
        return result
    finally: cli.protection_audit=original


if __name__=='__main__': main()
