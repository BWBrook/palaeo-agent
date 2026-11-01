"""Offline counterexamples for the pilot launch gate; synthetic files and process only."""
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from evaluation.pilot import launch

INVENTORY = ['mcp__worker__worker_execute']
USAGE = {'input_tokens': 2, 'cache_creation_input_tokens': 0, 'output_tokens': 3}


def content(*blocks):
    return {'message': {'content': list(blocks)}}


def tool_use():
    return {'type': 'tool_use', 'id': 'u1', 'name': INVENTORY[0], 'input': {'code': 'print(42)'}}


def fixture(root):
    materials = root / 'items/X/materials'
    materials.mkdir(parents=True)
    (materials / 'task.md').write_text('synthetic task after freeze\n')
    runtime = root / 'runtime'
    runtime.mkdir()
    (runtime / 'runtime.json').write_text('changed runtime manifest\n')
    prompts = root / 'prompts'
    prompts.mkdir()
    (prompts / 'analyst.md').write_text('changed prompt after freeze\n')
    (prompts / 'analyst-toolkit.md').write_text('toolkit\n')
    client = root / 'fake-client'
    client.write_text('synthetic binary, never executed\n')
    work = root / 'work'
    work.mkdir()
    plan = {'client_sha256': launch.sha(client), 'runtime_root': str(runtime),
            'runtime_manifest_sha256': 'stale-runtime-hash', 'items_dir': str(root / 'items'),
            'items_manifest_sha256': 'stale-materials-hash', 'prompts_sha256': {'analyst.md': 'stale-prompt-hash'},
            'inventory': {'direct': INVENTORY}, 'model': 'offline', 'work_root': str(work),
            'max_turns': 2, 'wall_seconds': 1}
    trial = {'trial_id': 'T001', 'item': 'X', 'arm': 'direct', 'block': 1}
    return plan, trial, client, prompts


def simulated_trial(root, *, init=True, usage=USAGE, export_link=False, cleanup_fail=False):
    plan, trial, client, prompts = fixture(root)
    events = ([{'type': 'system', 'subtype': 'init', 'tools': INVENTORY}] if init else [])
    events.append({'type': 'result', 'subtype': 'success', 'usage': usage})
    fake = type('Process', (), {'pid': 999999999, 'returncode': 0,
         'stdout': io.StringIO(''.join(json.dumps(e)+'\n' for e in events)), 'stderr': io.StringIO(''),
         'wait': lambda self, **kwargs: 0})()
    original_stage = launch.stage
    def stage(*args):
        result = original_stage(*args)
        if export_link:
            secret = root / 'outside-synthetic-secret.txt'
            secret.write_text('SYNTHETIC-OUTSIDE-CANARY\n')
            (args[0] / 'export-me.txt').symlink_to(secret)
        return result
    cleanup = (lambda marker: (_ for _ in ()).throw(launch.Halt('synthetic cleanup failure'))) if cleanup_fail else lambda marker: None
    with patch.object(launch, 'PROMPTS', prompts), patch.object(launch, 'client_path', lambda: client), \
         patch.object(launch, 'capture_inventory', lambda *args: INVENTORY), \
         patch.object(launch, 'stage', stage), patch.object(launch.subprocess, 'Popen', lambda *args, **kwargs: fake), \
         patch.object(launch.os, 'killpg', lambda *args: None), patch.object(launch, 'cleanup', cleanup), \
         patch.object(launch, 'score', lambda *args: {'outcome': 'correct', 'acceptable': True}):
        try:
            summary = launch.run_trial(trial, plan, root / 'out', 'SYNTHETIC-NEVER-TRANSMITTED')
        except launch.Halt as exc:
            return {'halt': str(exc), 'record_files': sorted(p.name for p in (root / 'out/trials/T001').iterdir())}
    saved = root / 'out/trials/T001/workspace/export-me.txt'
    return {'breach': summary['breach'], 'counted_tokens': summary['counted_tokens'],
            'reconciliation': summary['reconciliation'], 'exported_external_canary': saved.exists() and saved.read_text() == 'SYNTHETIC-OUTSIDE-CANARY\n',
            'copied_link_is_regular_file': saved.exists() and not saved.is_symlink()}


def main():
    findings = {}
    with tempfile.TemporaryDirectory(prefix='pilot-launch-review-') as scratch:
        root = Path(scratch)
        audit = root / 'audit'; audit.mkdir()
        wrong = {'request': {'tool': 'worker_write', 'path': 'unrelated.txt', 'content': 'wrong call'}, 'result': {'status': 'error'}}
        (audit / 'calls.jsonl').write_text(json.dumps(wrong)+'\n')
        findings['wrong_audit_and_missing_result_accepted'] = launch.reconcile([content(tool_use())], audit, INVENTORY)
        assert findings['wrong_audit_and_missing_result_accepted']['consistent']
        findings['unadvertised_success_rejected_positive_control'] = launch.reconcile([content({'type': 'tool_use', 'id': 'bad', 'name': 'Bash'})], root/'missing', INVENTORY)
        assert not findings['unadvertised_success_rejected_positive_control']['consistent']
        for state in ('started_only', 'unknown_usage', 'prior_boundary_breach'):
            folder = root / state
            record = folder/'trials/T001';record.mkdir(parents=True)
            (record/'started.json').write_text('{}')
            if state != 'started_only':
                (record/'trial.json').write_text(json.dumps({'counted_tokens': None if state=='unknown_usage' else 1, 'breach': ['init_inventory'] if state=='prior_boundary_breach' else []}))
            plan = {'trials': [{'trial_id': 'T001'}, {'trial_id': 'T002'}], 'counted_token_ceiling': 100}
            path = folder/'plan.json';path.write_text(json.dumps(plan))
            launched = []
            def fake_trial(trial, *args):
                launched.append(trial['trial_id'])
                return {'counted_tokens': 1, 'score': {'outcome': 'correct'}}
            with patch.object(launch,'run_trial',fake_trial):
                log=launch.run(path,folder,'SYNTHETIC')
            findings['resume_'+state] = {'launched': launched, 'log': log}
            assert launched == ['T002']
        for name, options in [('stale_pins', {}), ('missing_init', {'init':False}), ('incomplete_usage', {'usage':{'cache_read_input_tokens':100}}), ('export_symlink', {'export_link':True}), ('cleanup_failure_evidence', {'cleanup_fail':True})]:
            case=root/name;case.mkdir()
            findings[name]=simulated_trial(case, **options)
        assert findings['stale_pins']['counted_tokens']==5
        assert findings['missing_init']['breach']==[]
        assert findings['incomplete_usage']['counted_tokens']==0
        assert findings['export_symlink']['exported_external_canary'] and findings['export_symlink']['copied_link_is_regular_file']
        assert findings['cleanup_failure_evidence']['record_files']==['started.json']
        # A finite, owned process with the worker's interpreter/-I/-c argv shape.
        process_root=root/'cleanup-marker/trial';process_root.mkdir(parents=True)
        child=subprocess.Popen([sys.executable,'-I','-c','import time; time.sleep(15)'],cwd=process_root,start_new_session=True)
        try:
            probe=subprocess.run(['pgrep','-f',str(process_root)],capture_output=True,text=True)
            launch.cleanup(str(process_root))
            findings['cleanup_argv_marker']={'child_survived':child.poll() is None,'pgrep_status':probe.returncode,'pgrep_stderr':probe.stderr,'child_command_contains_marker':False,'kind':'finite synthetic process, not sandboxed worker'}
            assert child.poll() is None
        finally:
            child.kill();child.wait()
        # Budget stop within a four-trial block, despite balanced ordering.
        folder=root/'budget';folder.mkdir()
        plan={'trials':[{'trial_id':f'T{i:03}', 'block':1} for i in range(1,5)],'counted_token_ceiling':5}
        path=folder/'plan.json';path.write_text(json.dumps(plan)); launched=[]
        def costly(trial,*args):
            launched.append(trial['trial_id']);return {'counted_tokens':6,'score':{'outcome':'correct'}}
        with patch.object(launch,'run_trial',costly):log=launch.run(path,folder,'SYNTHETIC')
        findings['partial_balanced_block']={'launched':launched,'log':log,'completed_block':False}
    receipt={'baseline':'aedc1585a239abddea825f813d30c7fdfb91de17','live_clients':0,'provider_calls':0,'credentials_accessed':False,
        'method':'Direct production functions with mocked client/inventory/score; bounded owned process for argv-cleanup counterexample.',
        'source_sha256':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (ROOT/'evaluation/pilot/launch.py',ROOT/'evaluation/execution/worker.py',Path(__file__))},'observations':findings}
    (HERE/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps({'checks':len(findings),'receipt':str(HERE/'receipt.json'),'cleanup':findings['cleanup_argv_marker']}))

if __name__=='__main__':main()
