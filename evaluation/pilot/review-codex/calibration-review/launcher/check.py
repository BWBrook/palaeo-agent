"""Synthetic closure of L3/L4; inspect saved qualification without running its client/auth path."""
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[5]
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
from evaluation.pilot import launch


def main():
    checks=[]
    def record(name, passed):
        checks.append({'name':name,'passed':bool(passed)})
        assert passed,name
    with tempfile.TemporaryDirectory(prefix='L3-L4-closure-') as tmp:
        root=Path(tmp)
        runtime=root/'runtime';runtime.mkdir()
        base=root/'base';base.mkdir();(base/'python').write_text('synthetic interpreter')
        for arm in ('direct','toolkit'):
            site=runtime/arm/'lib/python3.12/site-packages';site.mkdir(parents=True)
            (site/'numpy.py').write_text('VALUE=1')
        client=root/'client';client.write_text('never run')
        items=root/'items';materials=items/'X/materials';materials.mkdir(parents=True)
        task=materials/'task.md';task.write_text('task')
        manifest=items/'MANIFEST.json'
        manifest.write_text(json.dumps({'X/materials/task.md':launch.sha(task)}))
        with patch.object(launch,'client_path',lambda:client),patch.object(launch,'UV_PYTHON',base):
            before=launch.fingerprints(runtime,items)
            dep=runtime/'direct/lib/python3.12/site-packages/numpy.py'
            dep.write_text('VALUE=2')
            record('installed_dependency_change_detected',launch.fingerprints(runtime,items)!=before)
            dep.write_text('VALUE=1')
            (base/'python').write_text('changed interpreter')
            record('base_interpreter_change_detected',launch.fingerprints(runtime,items)!=before)
        record('exact_material_positive',launch.verify_materials(items,'X')==[task])
        extra=materials/'extra.csv';extra.write_text('new data')
        try:launch.verify_materials(items,'X')
        except launch.Halt:record('extra_material_rejected',True)
        else:record('extra_material_rejected',False)
        extra.unlink();task.write_text('modified task')
        try:launch.verify_materials(items,'X')
        except launch.Halt:record('modified_material_rejected',True)
        else:record('modified_material_rejected',False)
        task.write_text('task');extra.symlink_to(task)
        try:launch.verify_materials(items,'X')
        except launch.Halt:record('material_symlink_rejected',True)
        else:record('material_symlink_rejected',False)
        audit=root/'audit';audit.mkdir()
        inventory=['mcp__worker__worker_write','mcp__worker__worker_read','mcp__worker__palaeo_discover']
        def reconcile(use, call, *, value=None, extra=None):
            (audit/'calls.jsonl').write_text(json.dumps(call)+'\n')
            result={'type':'tool_result','tool_use_id':use['id'],'is_error':False,
                    'content':json.dumps(call['result'] if value is None else value)}
            content=[use,result]+(extra or [])
            return launch.reconcile([{'message':{'content':content}}],audit,inventory)
        write={'type':'tool_use','id':'u1','name':inventory[0],'input':{'path':'answer.json','content':'EXPECTED'}}
        call={'request':{'tool':'worker_write','path':'answer.json','content':'EXPECTED'},'result':{'status':'ok','stdout':'ACTUAL'}}
        record('matching_full_write_accepted',reconcile(write,call)['consistent'])
        wrong=json.loads(json.dumps(call));wrong['request']['content']='DIFFERENT'
        record('changed_write_content_rejected',not reconcile(write,wrong)['consistent'])
        record('changed_returned_value_rejected',not reconcile(write,call,value={'status':'ok','stdout':'FORGED'})['consistent'])
        read={'type':'tool_use','id':'u2','name':inventory[1],'input':{'path':'x','offset':20,'limit':10}}
        readcall={'request':{'tool':'worker_read','path':'x','offset':0,'limit':100},'result':{'status':'ok','stdout':'ACTUAL'}}
        record('changed_read_range_rejected',not reconcile(read,readcall)['consistent'])
        defaultread={'type':'tool_use','id':'u3','name':inventory[1],'input':{'path':'x'}}
        readcall['request'].update(offset=0,limit=32768)
        record('default_read_normalised',reconcile(defaultread,readcall)['consistent'])
        orphan={'type':'tool_result','tool_use_id':'unknown','content':'orphan'}
        record('orphan_result_rejected',not reconcile(write,call,extra=[orphan])['consistent'])
        duplicate={'type':'tool_result','tool_use_id':'u1','content':json.dumps(call['result'])}
        record('duplicate_result_rejected',not reconcile(write,call,extra=[duplicate])['consistent'])
        record('duplicate_use_rejected',not reconcile(write,call,extra=[write])['consistent'])
        value={'status':'ok','methods':['synthetic']}
        tk={'type':'tool_use','id':'tk','name':inventory[2],'input':{}}
        tkcall={'request':{'tool':'discover','arguments':{}},'result':{'status':'ok','exit_code':0,'stdout':json.dumps(value)}}
        record('toolkit_adapter_value_accepted',reconcile(tk,tkcall,value=value)['consistent'])
        record('toolkit_forged_value_rejected',not reconcile(tk,tkcall,value={'status':'ok','methods':['forged']})['consistent'])
        config=root/'synthetic-config';config.mkdir()
        (config/'remote-settings.json').write_text('{}')
        (config/'remote-settings.json.signature-iat.json').write_text('{}')
        (config/'policy-limits.json').write_text(json.dumps({'restrictions':{'allow_product_feedback':{'allowed':False}}}))
        record('empty_managed_settings_accepted',bool(launch.verify_config_dir(config)['policy_limits_sha256']))
        (config/'remote-settings.json').write_text(json.dumps({'env':{'SYNTHETIC':'instruction'}}))
        try:launch.verify_config_dir(config)
        except launch.Halt:record('nonempty_managed_settings_rejected',True)
        else:record('nonempty_managed_settings_rejected',False)
        # No keychain symlink or credential file is created/opened. Mock only the status subprocess.
        home=root/'status-home';home.mkdir()
        seen={}
        def fake_status(*args,**kwargs):
            seen.update(kwargs)
            return type('R',(),{'stdout':json.dumps({'loggedIn':True,'authMethod':'claude.ai','subscriptionType':'team','apiProvider':'firstParty'})})()
        with patch.object(launch,'client_path',lambda:client),patch.object(launch.subprocess,'run',fake_status):
            result=launch.subscription_status(home,config)
        record('status_uses_launch_environment',seen['env']==launch.environment(home,config) and seen['cwd']==home)
    receipt=json.loads((ROOT/'evaluation/pilot/launch-evidence/supervisor-qualification.json').read_text())
    script=ROOT/'evaluation/pilot/qualify_supervisor.py'
    record('saved_qualification_script_matches',launch.sha(script)==receipt['script_sha256'])
    matches={name:launch.sha(ROOT/name)==digest for name,digest in receipt['fingerprints']['source'].items()}
    prompt_matches={name:launch.sha(ROOT/'evaluation/pilot/prompts'/name)==digest for name,digest in receipt['fingerprints']['prompts'].items()}
    record('saved_positive_control_present',receipt['cases'][1]['canary_config'] and receipt['cases'][1]['contents_preamble'])
    record('saved_verdict_all_true',all(receipt['verdict'].values()))
    qualification={'kind':'inspection of saved source-bound receipt, not a rerun',
      'recorded_verdict':receipt['verdict'],'recorded_inference_calls':receipt['inference_calls'],
      'source_matches_current':matches,'prompts_match_current':prompt_matches,
      'current_script_sha256':launch.sha(script)}
    payload={'baseline':'4a80b5f','checks':checks,'passed':sum(c['passed'] for c in checks),
      'live_client_calls':0,'provider_calls':0,'credential_access':False,'qualification':qualification,
      'source_sha256':{str(p.relative_to(ROOT)):launch.sha(p) for p in (Path(__file__),ROOT/'evaluation/pilot/launch.py',script,ROOT/'evaluation/pilot/launch-evidence/supervisor-qualification.json')}}
    (HERE/'receipt.json').write_text(json.dumps(payload,indent=2)+'\n')
    print(json.dumps({'passed':payload['passed'],'checks':len(checks),'receipt':str(HERE/'receipt.json')}))

if __name__=='__main__':main()
