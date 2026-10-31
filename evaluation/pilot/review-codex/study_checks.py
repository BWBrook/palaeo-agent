"""Independent synthetic study-integrity challenges; no pilot keys or generators."""
import argparse
import json
from pathlib import Path
import shutil

from palaeo_agent import run_study, inspect_study
from palaeo_agent.mcp_server import Transport


def check(root):
    root.mkdir(parents=True, exist_ok=False)
    material = root / 'materials'
    material.mkdir()
    (material/'data.dat').write_text('. x y\na 1 2\nb 2 3\nc 4 7\n')
    spec = {'study_version':1,'inputs':{'m':{'kind':'measurements','path':'data.dat','orientation':'samples_by_taxa'}},
            'datasets':{'d':{'source':'m'}},'analyses':[{'id':'r','dataset':'d','spec':{'method':'rma','format':'past','x':'x','y':'y','transform':'none','missing':'error'}}]}
    observations=[]
    directory=root/'missing-runs'
    run_study(spec,directory,base_dir=material)
    m=json.loads((directory/'manifest.json').read_text())
    m.update(status='complete',steps=[],runs={})
    (directory/'manifest.json').write_text(json.dumps(m))
    shutil.rmtree(directory/'runs')
    observations.append({'case':'complete_manifest_without_steps_or_runs','result':inspect_study(directory)})

    session=root/'session';session.mkdir()
    directory=session/'study'
    run_study(spec,directory,base_dir=material)
    outside=root/'outside-runs'
    (directory/'runs').rename(outside)
    (directory/'runs').symlink_to(outside,target_is_directory=True)
    observations.append({'case':'mcp_inspection_follows_outside_runs_symlink','session_root':str(session),
                         'outside':str(outside),'result':Transport(session).dispatch('study_inspect',{'study_dir':'study'})})

    (material/'counts.dat').write_text('. t1 t2 t3\na 2 4 8\nb 3 7 1\nc 9 1 2\nd 5 3 9\n')
    community={'method':'community','format':'past','orientation':'taxa_by_samples','value_type':'count',
               'transform':'none','distance':'braycurtis','dimensions':1,'missing':'error','empty_samples':'error'}
    counts={'study_version':1,'inputs':{'c':{'kind':'counts','path':'counts.dat','orientation':'samples_by_taxa'}},
            'datasets':{'d':{'source':'c'}},'analyses':[{'id':'a','dataset':'d','spec':community}]}
    outcome=run_study(counts,root/'orientation',base_dir=material)
    inspected=inspect_study(root/'orientation')
    observations.append({'case':'method_retransposes_canonical_dataset','input_samples':4,'outcome':outcome,
                         'result':inspected['runs']})

    partial=json.loads(json.dumps(spec))
    partial['datasets']={'bad':{'source':'m','operations':[{'op':'exclude','samples':['unknown'],'reason':'synthetic failure'}]},'later':{'source':'m'}}
    partial['analyses'][0]['dataset']='later'
    observations.append({'case':'later_dataset_not_recorded_as_not_run',
                         'result':run_study(partial,root/'partial',base_dir=material)})
    return observations


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('work',type=Path);parser.add_argument('receipt',type=Path)
    args=parser.parse_args()
    with args.receipt.open('x') as out:
        json.dump(check(args.work),out,indent=2);out.write('\n')
