"""Synthetic no-follow export challenge through the actual native worker."""
import hashlib
import json
from pathlib import Path
import shutil
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from evaluation.execution.worker import Worker
from evaluation.pilot.launch import UV_PYTHON

runtime = Path.home() / 'palaeo-eval/pilot-runtime-20261101/direct'
with tempfile.TemporaryDirectory(prefix='pilot-native-export-review-') as tmp:
    base = Path(tmp).resolve()
    trial = base/'trial'; trial.mkdir()
    secret = base/'outside-synthetic-secret.txt';secret.write_text('SYNTHETIC-OUTSIDE-CANARY\n')
    w=Worker(trial,runtime,runtime/'bin/python',base/'audit',trusted_read_roots=[UV_PYTHON])
    created=w.execute(f"from pathlib import Path; Path('export-me.txt').symlink_to({str(secret)!r}); print('link created')")
    denied=w.execute("print(open('export-me.txt').read())")
    shutil.copytree(trial,base/'recorded-workspace',ignore=shutil.ignore_patterns('.worker'))
    exported=(base/'recorded-workspace/export-me.txt').read_text()
    assert created['status']=='ok' and denied['status']=='error' and 'PermissionError' in denied['stderr']
    assert exported == secret.read_text()
    result={'worker_created_link':created,'worker_read_denied':denied,'supervisor_exported_external_canary':True,
            'saved_path_is_regular_file':not (base/'recorded-workspace/export-me.txt').is_symlink(),
            'provider_calls':0,'credentials_accessed':False,'runtime':str(runtime),
            'runtime_manifest_sha256':hashlib.sha256((runtime.parent/'runtime.json').read_bytes()).hexdigest(),
            'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
(HERE/'native-link-receipt.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'worker_created_link':True,'worker_read_denied':True,'supervisor_exported_external_canary':True}))
