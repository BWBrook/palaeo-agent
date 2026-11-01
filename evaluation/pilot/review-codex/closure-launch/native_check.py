"""Native closure of export and registered-group cleanup with synthetic data only."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT=Path(__file__).resolve().parents[4]
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
from evaluation.execution.worker import Worker
from evaluation.pilot import launch

runtime=Path.home()/'palaeo-eval/pilot-runtime-20261101/direct'
with tempfile.TemporaryDirectory(prefix='closure-native-') as tmp:
    base=Path(tmp).resolve();trial=base/'trial';trial.mkdir()
    secret=base/'outside-canary.txt';secret.write_text('SYNTHETIC-OUTSIDE-CANARY')
    worker=Worker(trial,runtime,runtime/'bin/python',base/'audit',trusted_read_roots=[launch.UV_PYTHON])
    made=worker.execute(f"from pathlib import Path; Path('export-me.txt').symlink_to({str(secret)!r}); Path('ordinary.txt').write_text('ordinary')")
    denied=worker.execute("print(open('export-me.txt').read())")
    refused=launch.export(trial,base/'export')
    assert made['status']=='ok' and denied['status']=='error'
    assert refused[0]['path']=='export-me.txt'
    assert not (base/'export/export-me.txt').exists()
    assert (base/'export/ordinary.txt').read_text()=='ordinary'
    pids=[json.loads(l) for l in (base/'audit/pids.jsonl').read_text().splitlines()]
    assert len(pids)==2 and not launch.living_groups({x['pgid'] for x in pids})
    child=subprocess.Popen([sys.executable,'-I','-c','import time; time.sleep(30)'],cwd=trial,start_new_session=True)
    cleanup=base/'cleanup';cleanup.mkdir()
    (cleanup/'pids.jsonl').write_text(json.dumps({'pgid':child.pid})+'\n')
    try:
        groups=launch.terminate(None,cleanup)
        code=child.wait(timeout=3)
        assert code == -9 and not launch.living_groups(set(groups))
    finally:
        if child.poll() is None:child.kill();child.wait()
    payload={'baseline':'2cbe718','worker_created_external_link':True,'worker_external_read_denied':True,
        'export_refused_link':True,'ordinary_exported':True,'refused_exports':refused,
        'worker_pid_records':len(pids),'normal_worker_groups_gone':True,
        'registered_separate_group_killed':code==-9,'provider_calls':0,'client_launches':0,'credentials_accessed':False,
        'runtime_manifest_sha256':launch.sha(runtime.parent/'runtime.json'),
        'source_sha256':{str(p.relative_to(ROOT)):launch.sha(p) for p in (Path(__file__),ROOT/'evaluation/pilot/launch.py',ROOT/'evaluation/execution/worker.py')}}
(HERE/'native-receipt.json').write_text(json.dumps(payload,indent=2)+'\n')
print(json.dumps({k:v for k,v in payload.items() if isinstance(v,bool)}))
