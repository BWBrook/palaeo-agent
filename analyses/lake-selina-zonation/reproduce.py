"""Reproduce copied native bundles in a fresh worker with original application paths blocked."""

import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

HERE=Path(__file__).resolve().parent
CHILD=r'''
import hashlib,json,pathlib,sys
from unittest.mock import patch
import palaeo_agent as pa
root,case,prior=map(pathlib.Path,sys.argv[1:])
original_open=pathlib.Path.open
attempts=[]
def guarded_open(path,*args,**kwargs):
    if any(path.resolve().is_relative_to(forbidden) for forbidden in (case,prior)):
        attempts.append(str(path));raise OSError('Original application paths blocked')
    return original_open(path,*args,**kwargs)
records={}
with patch.object(pathlib.Path,'open',guarded_open):
    try:
        (case/'data/archive.tsv').read_bytes()
    except OSError:
        pass
    else:
        raise AssertionError('Original-path guard did not work')
    attempts.clear()
    for label in ('zonation','plot'):
        old=root/f'copied-{label}';new=root/f'reproduced-{label}'
        outcome=pa.reproduce_study(old,new)
        assert outcome['status']=='reproduced',outcome
        before=json.loads((old/'manifest.json').read_bytes());after=json.loads((new/'manifest.json').read_bytes())
        hashes={}
        for name,item in before['runs'].items():
            a=(old/item['run_dir']/'results.json').read_bytes()
            b=(new/after['runs'][name]['run_dir']/'results.json').read_bytes()
            assert a==b,name
            hashes[name]=hashlib.sha256(b).hexdigest()
        records[label]={'status':outcome['status'],'derived_identical':outcome['derived_identical'],'byte_identical_results':hashes}
    extracted=pa.reproduce_neotoma(root/'copied-extraction',root/'reproduced-extraction')
    assert extracted['status']=='reproduced',extracted
    assert not attempts
print(json.dumps({'studies':records,'extraction_status':extracted['status'],'original_path_probe_refused':True,
                  'original_path_read_attempts':len(attempts)}))
'''


def main():
    provenance=json.loads((HERE/'provenance.json').read_text())
    intake=json.loads((HERE/'intake-check.json').read_text())
    with tempfile.TemporaryDirectory(prefix='palaeo-zonation-reproduction-') as temp:
        root=Path(temp)
        for label,path in [('zonation',provenance['study_dir']),('plot',provenance['plot_study_dir']),
                           ('extraction',intake['extraction_bundle'])]:
            shutil.copytree(HERE/path,root/f'copied-{label}')
        completed=subprocess.run([sys.executable,'-c',CHILD,str(root),str(HERE),str(HERE.parent/'lake-selina')],
                                 cwd=root,check=True,capture_output=True,text=True)
        checked=json.loads(completed.stdout)
    receipt={'freeze_commit':provenance['freeze_commit'],'portable_bundles':checked,
             'exports':[{'file':name,'sha256':hashlib.sha256((HERE/name).read_bytes()).hexdigest()}
                        for name in ('results.json','boundaries.csv','boundary-offsets.csv')],
             'scope':'All five complete native child results reproduce byte for byte; copied extraction reproduces; original application paths blocked; interpretation not validated'}
    (HERE/'reproduction-check.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps(receipt,indent=2))


if __name__=='__main__':
    main()
