"""Close F7 using independent unit arithmetic and saved-package checks."""
import ast
import csv
import hashlib
import json
import math
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

from palaeo_agent import inspect_study, reproduce_study, run_study

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
ITEMS=ROOT/'evaluation/pilot/items'


def main():
    frozen=json.loads((ROOT/'evaluation/pilot/flaws.json').read_text())
    rows=list(csv.DictReader((ITEMS/'P07-control/materials/shells.csv').open()))
    x=[float(r['length'])*(10 if r['locality']=='L3' else 1) for r in rows]
    y=[float(r['width'])*(10 if r['locality']=='L3' else 1) for r in rows]
    mx,my=math.fsum(x)/len(x),math.fsum(y)/len(y)
    xx=math.fsum((a-mx)**2 for a in x); yy=math.fsum((a-my)**2 for a in y)
    xy=math.fsum((a-mx)*(b-my) for a,b in zip(x,y))
    slope=math.copysign(math.sqrt(yy/xx),xy)
    own={'slope':slope,'intercept':my-slope*mx,'n':len(x),'mean_length_mm':mx}
    errors={k:abs(v-frozen['P07-control']['results'][k]) for k,v in own.items()}
    assert max(errors.values())<1e-12
    previous=json.loads(subprocess.check_output(['git','show','aedc158:evaluation/pilot/flaws.json'],cwd=ROOT,text=True))
    assert all(previous[k]['results']==frozen[k]['results'] for k in frozen if k!='P07-control')
    assert all(isinstance(v.get('attribution_criterion'),str) and v['attribution_criterion'].strip() for v in frozen.values())
    source=ROOT/'tests/test_pilot_flaws.py'
    tree=ast.parse(source.read_text())
    scripts={n.targets[0].id:ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign)
             and isinstance(n.targets[0],ast.Name) and n.targets[0].id in {'P12_SCRIPT','P10_SCRIPT'}}
    observations=[]
    with tempfile.TemporaryDirectory(prefix='flaw-closure-') as tmp:
        root=Path(tmp)
        for item,name,old,new in [
            ('P12-control','P12_SCRIPT','TRANSFORM = "relative"','TRANSFORM = "raw"'),
            ('P10-control','P10_SCRIPT','CLAIM = ""','CLAIM = '+repr(frozen['P10-control']['answer_edits']['summary_append']))]:
            work=root/item;work.mkdir();shutil.copytree(ITEMS/item/'materials',work/'materials')
            script=work/'analysis.py';script.write_text(scripts[name].replace(old,new))
            subprocess.run([sys.executable,str(script)],cwd=work,check=True)
            before=(work/'answer.json').read_bytes();answer=json.loads(before)
            subprocess.run([sys.executable,str(script)],cwd=work,check=True)
            assert before==(work/'answer.json').read_bytes()
            assert all(abs(answer['results'][k]-v)<1e-12 for k,v in frozen[item]['results'].items())
            if item=='P10-control':assert answer['summary'].endswith(frozen[item]['answer_edits']['summary_append'])
            observations.append({'case':'direct_'+item,'byte_identical_rerun':True,'results':answer['results'],
                                 'summary':answer['summary'],'analysis_sha256':hashlib.sha256(script.read_bytes()).hexdigest()})
        work=root/'toolkit';work.mkdir()
        shutil.copytree(ITEMS/'P10-control/materials',work/'materials')
        spec={'method':'community','format':'past','orientation':'samples_by_taxa','value_type':'count','transform':'none',
              'distance':'braycurtis','dimensions':1,'missing':'error','empty_samples':'error'}
        study={'study_version':1,'inputs':{'c':{'kind':'counts','path':str(work/'materials/counts.tsv'),'orientation':'samples_by_taxa'}},
               'datasets':{'d':{'source':'c'}},'analyses':[{'id':'a','dataset':'d','spec':spec}]}
        run=run_study(study,work/'study');verified=inspect_study(run['study_dir'])
        record=json.loads((Path(run['study_dir'])/verified['runs']['a']['run_dir']/'results.json').read_text())
        hs={r['sample_id']:r['shannon'] for r in record['diversity']}
        change=hs['S12']-hs['S1'];assert abs(change-frozen['P10-control']['results']['shannon_change'])<1e-12
        answer={'status':'completed','results':{'shannon_change':change},'assumptions':[],'exclusions':[],'issues':[],
                'summary':'Toolkit community run; S1 is oldest. '+frozen['P10-control']['answer_edits']['summary_append']}
        path=work/'answer.json';path.write_text(json.dumps(answer));before=path.read_bytes()
        reproduced=reproduce_study(work/'study',root/'reproduced')
        assert verified['status']=='verified' and reproduced['status']=='reproduced'
        assert path.read_bytes()==before
        observations.append({'case':'toolkit_P10-control','inspect':verified['status'],'reproduce':reproduced['status'],
                             'answer_unchanged':True,'answer':answer,
                             'integrity_scope':'Study numerical bundle. External answer prose remains a scientific adjudication, not something inspect certifies.'})
    files=[Path(__file__),ROOT/'evaluation/pilot/flaws.py',ROOT/'evaluation/pilot/flaws.json',source,
           ITEMS/'P07-control/materials/shells.csv',ITEMS/'P07-control/materials/dictionary.md',ITEMS/'P07-control/materials/task.md']
    receipt={'baseline':'2cbe718','P07_independent':own,'P07_absolute_errors':errors,'other_11_reference_values_unchanged':True,
             'attribution_criteria_count':len(frozen),'observations':observations,'inference_calls':0,
             'source_sha256':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files}}
    (HERE/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps({'P07_max_absolute_error':max(errors.values()),'saved_package_checks':len(observations),'attribution_criteria':len(frozen)}))


if __name__=='__main__':main()
