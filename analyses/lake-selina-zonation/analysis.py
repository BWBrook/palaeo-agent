"""Run the prospectively frozen four-zonation study and export inspected API fields."""

import argparse
import csv
import hashlib
import json
from pathlib import Path
import subprocess

import palaeo_agent as pa

HERE=Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path,value):
    path.write_text(json.dumps(value,indent=2)+'\n')


def cut(result,k):
    return [record for record in result['boundaries'] if record['split_rank']<k]


def pair(record):
    return record['left_id'],record['right_id']


def compare(primary,result,k):
    reference=cut(primary,primary['retention']['selected_zones'])
    current=cut(result,k)
    reference_pairs={pair(b) for b in reference}; current_pairs={pair(b) for b in current}
    persistent=[b for b in current if pair(b) in reference_pairs]
    unmatched=[b for b in current if pair(b) not in reference_pairs]
    offsets=[]
    if reference:
        for boundary in unmatched:
            nearest=min(reference,key=lambda b:(abs(b['boundary']-boundary['boundary']),b['boundary']))
            offsets.append({'sensitivity_left_id':boundary['left_id'],'sensitivity_right_id':boundary['right_id'],
                'primary_left_id':nearest['left_id'],'primary_right_id':nearest['right_id'],
                'gap_offset':boundary['boundary']-nearest['boundary'],
                'left_depth_offset_cm':boundary['left_position']-nearest['left_position'],
                'right_depth_offset_cm':boundary['right_position']-nearest['right_position']})
    return {'k':k,'boundaries':current,'persistent':persistent,
            'unmatched_primary':[b for b in reference if pair(b) not in current_pairs],
            'unmatched_sensitivity':unmatched,'nearest_offsets':offsets}


def csv_export(path,fields,rows):
    with path.open('w',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=fields,lineterminator='\n')
        writer.writeheader();writer.writerows(rows)


def verified_study(spec_path,directory):
    outcome=pa.run_study(spec_path,directory)
    assert outcome['status']=='complete',outcome
    assert pa.inspect_study(directory)['status']=='verified'
    manifest=json.loads((directory/'manifest.json').read_bytes())
    records={name:pa.inspect_run(directory/item['run_dir']) for name,item in manifest['runs'].items()}
    return manifest,records


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--output',type=Path,default=HERE/'runs-study')
    args=parser.parse_args()
    lock=json.loads((HERE/'input-lock.json').read_text())
    assert pa.primer()['sha256']==lock['primer']['sha256']
    assert all(sha(HERE/item['file'])==item['sha256'] for item in lock['files'])
    repo=HERE.parents[1]
    freeze=subprocess.check_output(['git','log','-1','--format=%H','--','analyses/lake-selina-zonation/DESIGN.md'],cwd=repo,text=True).strip()
    assert freeze,'Commit the design before any zonation'
    for name in ['DESIGN.md','input-lock.json',*[item['file'] for item in lock['files']]]:
        committed=subprocess.check_output(['git','show',f'{freeze}:analyses/lake-selina-zonation/{name}'],cwd=repo)
        assert committed==(HERE/name).read_bytes(),name
    directory=args.output.resolve()
    manifest,records=verified_study(HERE/'study.json',directory)
    expected={'archive_hellinger','repaired_hellinger','archive_relative','repaired_relative'}
    assert set(records)==expected
    results={name:item['result'] for name,item in records.items()}
    primary=results['archive_hellinger']; primary_k=primary['retention']['selected_zones']
    assert primary['n']==72 and primary['n_taxa']==60
    for result in results.values():
        assert result['sample_ids']==primary['sample_ids'] and result['taxon_ids']==primary['taxon_ids']
        assert result['positions']==primary['positions'] and result['excluded']==[]
    plot_directory=directory.with_name(directory.name+'-plot')
    plot_manifest,plot_records=verified_study(HERE/'plot-study.json',plot_directory)
    plot=plot_records['plot_composition']['result']
    assert plot['sample_ids']==primary['sample_ids'] and plot['taxon_ids']==primary['taxon_ids']
    assert plot['retained_counts']==primary['retained_counts']
    assert (directory/'derived/archive.dat').read_bytes()==(plot_directory/'derived/archive.dat').read_bytes()
    comparisons={mode:{name:compare(primary,result,result['retention']['selected_zones'] if mode=='selected' else primary_k)
                       for name,result in results.items()} for mode in ('selected','common_primary_k')}
    plot_fields=('method','method_version','sample_ids','taxon_ids','value_type','transform','transformed_matrix','warnings','limitations')
    write_json(HERE/'results.json',{'primer':lock['primer'],'coniss':results,'plot':{k:plot[k] for k in plot_fields},
                                   'comparisons':comparisons})
    boundaries=[];offsets=[]
    for mode,analyses in comparisons.items():
        for name,record in analyses.items():
            persistent={pair(b) for b in record['persistent']}
            boundaries.extend({'mode':mode,'analysis_id':name,'k':record['k'],**b,'persists':pair(b) in persistent} for b in record['boundaries'])
            offsets.extend({'mode':mode,'analysis_id':name,**offset} for offset in record['nearest_offsets'])
    csv_export(HERE/'boundaries.csv',['mode','analysis_id','k','boundary','left_id','right_id','left_position','right_position','merge_step','split_rank','persists'],boundaries)
    csv_export(HERE/'boundary-offsets.csv',['mode','analysis_id','sensitivity_left_id','sensitivity_right_id','primary_left_id','primary_right_id','gap_offset','left_depth_offset_cm','right_depth_offset_cm'],offsets)
    provenance={'freeze_commit':freeze,'implementation_commit':lock['implementation_commit'],'study_dir':str(directory.relative_to(HERE)),
        'plot_study_dir':str(plot_directory.relative_to(HERE)),'studies':{},'runs':{}}
    for label,folder,m,items in [('zonation',directory,manifest,records),('plot',plot_directory,plot_manifest,plot_records)]:
        provenance['studies'][label]={'manifest_sha256':sha(folder/'manifest.json')}
        for name,record in items.items():
            provenance['runs'][name]={'study':label,'run_dir':m['runs'][name]['run_dir'],'run_id':record['manifest']['run_id'],
                'results_sha256':sha(folder/m['runs'][name]['run_dir']/'results.json'),'environment':record['environment']}
    write_json(HERE/'provenance.json',provenance)
    print(json.dumps({name:{'selected_zones':r['retention']['selected_zones'],'total_dispersion':r['total_dispersion'],
                            'boundaries':[(b['left_position'],b['right_position']) for b in comparisons['selected'][name]['boundaries']],
                            'warnings':r['warnings']} for name,r in results.items()},indent=2))


if __name__=='__main__':
    main()
