"""Verify the original prospective file set; additions do not redefine its freeze."""
import argparse,json
from pathlib import Path
from hashlib import sha256
import v05_replay as original

def main():
    p=argparse.ArgumentParser();p.add_argument('--verify-only',action='store_true')
    p.add_argument('--output-dir',default='results/v0.5/reproduced');a=p.parse_args()
    snapshot=original.OUT/'experiment_snapshot.json';frozen=json.loads(snapshot.read_text())
    for name,h in frozen['hashes'].items():
        if sha256((original.ROOT/name).read_bytes()).hexdigest()!=h:raise AssertionError(name)
    print('Historical files:',original.check_preservation(),'frozen source files:',len(frozen['hashes']))
    if a.verify_only:return
    destination=original.ROOT/a.output_dir
    if destination.resolve()==(original.OUT/'raw').resolve():raise ValueError('Preserve original raw results')
    shared={}
    for path in sorted((original.ROOT/'results/v0.4/raw').glob('primary*--v04--*.json.gz')):
        out=destination/path.name
        if out.exists():raise FileExistsError(out)
        result=original.replay(path,shared)
        result['experiment_snapshot_sha256']=sha256(snapshot.read_bytes()).hexdigest()
        original.dump(out,result);print(path.name,flush=True)

if __name__=='__main__':main()
