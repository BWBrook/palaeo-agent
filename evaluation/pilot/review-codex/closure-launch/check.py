"""Independent offline closure checks for L1-L8; no clients or credentials."""
import hashlib
import io
import json
from pathlib import Path
import sys
import tempfile
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[4]
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
from evaluation.pilot import launch

INV=['mcp__worker__worker_execute','mcp__worker__worker_read','mcp__worker__worker_write']
USAGE={k:0 for k in launch.USAGE_FIELDS}
USAGE.update(input_tokens=2,output_tokens=3)


def fixture(base):
    materials=base/'items/X/materials';materials.mkdir(parents=True)
    task=materials/'task.md';task.write_text('synthetic task')
    manifest=base/'items/MANIFEST.json';manifest.write_text(json.dumps({'X/materials/task.md':launch.sha(task)}))
    runtime=base/'runtime'
    for arm in ('direct','toolkit'):
        site=runtime/arm/'lib/python3.12/site-packages'
        (site/'numpy').mkdir(parents=True)
        (site/'numpy/core.py').write_text('synthetic_dependency=1\n')
        (runtime/arm/'pyvenv.cfg').write_text('synthetic config\n')
        if arm=='toolkit':
            (site/'palaeo_agent').mkdir()
            (site/'palaeo_agent/__init__.py').write_text('synthetic_toolkit=1\n')
    (runtime/'runtime.json').write_text('{}')
    prompts=base/'prompts';prompts.mkdir()
    (prompts/'analyst.md').write_text('synthetic prompt')
    (prompts/'analyst-toolkit.md').write_text('toolkit')
    client=base/'client';client.write_text('never executed')
    config=base/'config';config.mkdir()
    (base/'work').mkdir()
    plan={'runtime_root':str(runtime),'items_dir':str(base/'items'),'config_dir':str(config),
          'capture_config_dir':str(config),'inventory':{'direct':INV},'model':'offline',
          'work_root':str(base/'work'),'wall_seconds':1,'max_turns':2}
    return plan,client,prompts


def simulate(base, *, init=True, usage=USAGE, cleanup_failure=False):
    plan,client,prompts=fixture(base)
    events=([{'type':'system','subtype':'init','tools':INV}] if init else [])
    events.append({'type':'result','usage':usage,'subtype':'success'})
    fake=type('FakeProcess',(),{'pid':999999999,'returncode':0,'stdout':io.StringIO(''.join(json.dumps(e)+'\n' for e in events)),
          'stderr':io.StringIO(''),'wait':lambda self,**kwargs:0})()
    termination=(lambda *args:(_ for _ in ()).throw(launch.Halt('synthetic cleanup failure'))) if cleanup_failure else lambda *args:[]
    with patch.object(launch,'client_path',lambda:client),patch.object(launch,'PROMPTS',prompts), \
         patch.object(launch,'capture_inventory',lambda *args:INV),patch.object(launch.subprocess,'Popen',lambda *args,**kwargs:fake), \
         patch.object(launch,'terminate',termination),patch.object(launch,'score',lambda *args:{'outcome':'correct','acceptable':True}):
        plan['fingerprints']=launch.fingerprints(plan['runtime_root'],plan['items_dir'])
        try:
            result=launch.run_trial({'trial_id':'T001','item':'X','arm':'direct'},plan,base/'out',api_key='OFFLINE',base_url='http://127.0.0.1:9')
            outcome={'returned':True,'complete':result['complete']}
        except launch.Halt as exc:outcome={'halt':str(exc)}
    record=base/'out/trials/T001'
    outcome['record_files']=sorted(p.name for p in record.iterdir())
    outcome['saved_summary']=json.loads((record/'trial.json').read_text())
    return outcome


def main():
    obs={}
    with tempfile.TemporaryDirectory(prefix='closure-launch-') as tmp:
        root=Path(tmp)
        base=root/'pins';base.mkdir()
        plan,client,prompts=fixture(base)
        with patch.object(launch,'client_path',lambda:client),patch.object(launch,'PROMPTS',prompts):
            original=launch.fingerprints(plan['runtime_root'],plan['items_dir'])
            dep=Path(plan['runtime_root'])/'direct/lib/python3.12/site-packages/numpy/core.py'
            dep.write_text('synthetic_dependency=999\n')
            obs['changed_dependency_undetected']=launch.fingerprints(plan['runtime_root'],plan['items_dir'])==original
            assert obs['changed_dependency_undetected']
            (prompts/'analyst.md').write_text('changed prompt')
            obs['changed_prompt_detected']=launch.fingerprints(plan['runtime_root'],plan['items_dir'])!=original
            assert obs['changed_prompt_detected']
        extra=base/'items/X/materials/extra-reference.csv';extra.write_text('new,material\n')
        launch.verify_materials(base/'items','X')
        launch.stage(base/'staged/trial',base/'items/X/materials',base/'runtime','direct',base/'audit')
        obs['unlisted_material_staged']=(base/'staged/trial/extra-reference.csv').read_bytes()==extra.read_bytes()
        assert obs['unlisted_material_staged']
        (base/'items/X/materials/task.md').write_text('changed task')
        try:launch.verify_materials(base/'items','X')
        except launch.Halt:obs['changed_listed_material_rejected']=True
        else:raise AssertionError('listed material mutation accepted')
        audit=root/'reconcile';audit.mkdir()
        use={'type':'tool_use','id':'u1','name':'mcp__worker__worker_write','input':{'path':'answer.json','content':'EXPECTED'}}
        result={'type':'tool_result','tool_use_id':'u1','content':'FABRICATED OUTPUT','is_error':False}
        call={'request':{'tool':'worker_write','path':'answer.json','content':'DIFFERENT'},'result':{'status':'ok','stdout':'ACTUAL OUTPUT'}}
        (audit/'calls.jsonl').write_text(json.dumps(call)+'\n')
        events=[{'message':{'content':[use,result]}}]
        obs['different_write_content_and_output_accepted']=launch.reconcile(events,audit,INV)
        assert obs['different_write_content_and_output_accepted']['consistent']
        obs['missing_result_rejected']=not launch.reconcile([{'message':{'content':[use]}}],audit,INV)['consistent']
        assert obs['missing_result_rejected']
        use2={'type':'tool_use','id':'u1','name':'mcp__worker__worker_read','input':{'path':'x','offset':20,'limit':10}}
        call2={'request':{'tool':'worker_read','path':'x','offset':0,'limit':100},'result':{'status':'ok','stdout':'ACTUAL'}}
        (audit/'calls.jsonl').write_text(json.dumps(call2)+'\n')
        obs['different_read_range_accepted']=launch.reconcile([{'message':{'content':[use2,result]}}],audit,INV)
        assert obs['different_read_range_accepted']['consistent']
        orphan={'type':'tool_result','tool_use_id':'unknown','content':'orphan'}
        (audit/'calls.jsonl').write_text('')
        obs['orphan_result_accepted']=launch.reconcile([{'message':{'content':[orphan]}}],audit,INV)
        assert obs['orphan_result_accepted']['consistent']
        for state in ('started_only','incomplete','halted','wrong_plan'):
            folder=root/state;(folder/'trials/T001').mkdir(parents=True)
            if state=='incomplete':(folder/'trials/T001/trial.json').write_text(json.dumps({'complete':False,'counted_tokens':None}))
            if state=='halted':(folder/'HALTED.json').write_text('{}')
            if state=='wrong_plan':(folder/'PLAN.sha256').write_text('other')
            try:launch.ledger(folder,'expected')
            except launch.Halt as exc:obs['ledger_'+state]={'rejected':True,'reason':str(exc)}
            else:raise AssertionError(state)
        for name,options in [('positive_complete',{}),('missing_init',{'init':False}),('incomplete_usage',{'usage':{'cache_read_input_tokens':5}}),('cleanup_failure',{'cleanup_failure':True})]:
            base=root/name;base.mkdir();obs[name]=simulate(base,**options)
        assert obs['positive_complete']['complete']
        assert 'no_init_record' in obs['missing_init']['halt']
        assert 'usage complete False' in obs['incomplete_usage']['halt']
        assert 'transcript.jsonl' in obs['cleanup_failure']['record_files']
        assert not obs['cleanup_failure']['saved_summary']['complete']
    payload={'baseline':'2cbe718','method':'Synthetic fixtures and direct production function calls; clients/auth/inventory captured functions mocked; no credentials opened.',
             'provider_calls':0,'client_launches':0,'observations':obs,
             'source_sha256':{str(p.relative_to(ROOT)):launch.sha(p) for p in (Path(__file__),ROOT/'evaluation/pilot/launch.py',ROOT/'evaluation/execution/worker.py',ROOT/'evaluation/execution/server.py')}}
    (HERE/'receipt.json').write_text(json.dumps(payload,indent=2)+'\n')
    print(json.dumps({'observations':len(obs),'receipt':str(HERE/'receipt.json')}))

if __name__=='__main__':main()
