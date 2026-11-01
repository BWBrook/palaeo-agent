import sys,json,hashlib,stat,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[5]
sys.path.insert(0,str(ROOT))
from evaluation.pilot import launch
from palaeo_agent.runs import inspect_run,reproduce
from palaeo_agent.study import inspect_study,reproduce_study
BASE=ROOT/'evaluation/pilot/run-records'
rows=[]
for run in sorted(BASE.glob('pilot-*')):
    plan=json.loads(next(run.glob('*.plan.json')).read_text())
    for p in sorted(run.glob('trials/*/trial.json')):
        d=json.loads(p.read_text()); start=json.loads((p.parent/'started.json').read_text())
        transcript=p.parent/'transcript.jsonl'
        events=[json.loads(s) for s in transcript.read_text().splitlines()] if transcript.exists() else []
        rec=launch.reconcile(events,p.parent/'worker-audit',plan['inventory'][d['trial']['arm']]) if events else None
        workspace=p.parent/'workspace'
        row={'record':str(p.parent.relative_to(BASE)),'trial':d['trial'],'complete':d['complete'],'client_launched':bool(events),'counted_tokens':d.get('counted_tokens'),'elapsed_seconds':d.get('finished_unix',start['started_unix'])-start['started_unix'],'reconciliation':rec,'matches_saved_reconciliation':rec==d.get('reconciliation'),'scripts':[str(s.relative_to(workspace)) for s in workspace.rglob('*.py')],'studies':[str(s.parent.relative_to(workspace)) for s in workspace.rglob('study.json')],'runs':[str(s.parent.relative_to(workspace)) for s in workspace.rglob('spec.json')]}
        rows.append(row)
q=json.loads((ROOT/'evaluation/pilot/launch-evidence/supervisor-qualification.json').read_text())
hashes={k:hashlib.sha256((ROOT/k).read_bytes()).hexdigest()==v for k,v in q['fingerprints']['source'].items()}
hashes.update({'prompt/'+k:hashlib.sha256((ROOT/'evaluation/pilot/prompts'/k).read_bytes()).hexdigest()==v for k,v in q['fingerprints']['prompts'].items()})
hashes['qualification_script']=hashlib.sha256((ROOT/'evaluation/pilot/qualify_supervisor.py').read_bytes()).hexdigest()==q['script_sha256']
current=launch.fingerprints(plan['runtime_root'],ROOT/'evaluation/pilot/items')
full_hashes={k:current[k]==v for k,v in q['fingerprints'].items()}
archive_comparison={}
for folder in sorted(BASE.glob('pilot-*')):
    matched=0; missing=[]; different=[]
    for p in folder.rglob('*'):
        if not p.is_file(): continue
        rel=p.relative_to(folder)
        original=Path('/Users/bwbrook/palaeo-eval')/folder.name/rel
        if not original.is_file() and len(rel.parts)==1:
            original=Path('/Users/bwbrook/palaeo-eval')/rel
        if not original.is_file(): missing.append(str(rel))
        elif p.read_bytes()!=original.read_bytes(): different.append(str(rel))
        else: matched+=1
    archive_comparison[folder.name]={'matched':matched,'missing_at_original':missing,'different':different}
special=[str(p.relative_to(BASE)) for p in BASE.rglob('*') if not (stat.S_ISREG(p.lstat().st_mode) or stat.S_ISDIR(p.lstat().st_mode))]
reproductions=[]
with tempfile.TemporaryDirectory(prefix='palaeo-closeout-repro-') as temp:
 for row in rows:
    ws=BASE/row['record']/'workspace'
    for kind,paths in [('study',row['studies']),('run',row['runs'])]:
      for path in paths:
       original=ws/path
       try:
        inspect=(inspect_study if kind=='study' else inspect_run)(original)
        result=(reproduce_study if kind=='study' else reproduce)(original,Path(temp)/str(len(reproductions)))
        environment_difference=None
        if kind=='run':
            a=json.loads((original/'environment.json').read_text())
            b=json.loads((Path(result['new_run'])/'environment.json').read_text())
            environment_difference={k:{'original':a[k],'reproduction':b[k]} for k in a if a[k]!=b[k]}
        result={k:v for k,v in result.items() if k not in ('original','new','original_run','new_run')}
        reproductions.append({'bundle':str(original.relative_to(BASE)),'kind':kind,'verified':True,'result':result,'study_status':inspect.get('study_status'),'environment_difference':environment_difference})
       except Exception as e:
        reproductions.append({'bundle':str(original.relative_to(BASE)),'kind':kind,'error':type(e).__name__+': '+str(e)})
receipt={'reviewed_commit':'0c3e106','trial_records':rows,'totals':{'executed':sum(r['client_launched'] for r in rows),'complete':sum(r['complete'] for r in rows),'preflight_halts':sum(not r['client_launched'] for r in rows),'integration_tokens':sum(r['counted_tokens'] or 0 for r in rows if 'integration' in r['record']),'calibration_tokens':sum(r['counted_tokens'] or 0 for r in rows if 'calibration' in r['record'])},'qualification_source_hashes_match':hashes,'qualification_verdict':q['verdict'],'archive_special_files':special,'reproductions':reproductions,'live_model_calls':0}
receipt.update(qualification_runtime_hashes_match=full_hashes,archive_source_comparison=archive_comparison)
(Path(__file__).parent/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps({k:v for k,v in receipt.items() if k not in ('trial_records','reproductions')},indent=2))
print(json.dumps(reproductions,indent=2))
