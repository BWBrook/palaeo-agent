"""Prepare the frozen inputs via saved-Neotoma extraction and study operations; never compute zonation."""

import csv
from decimal import Decimal
import hashlib
import json
from pathlib import Path
from unittest.mock import patch

import palaeo_agent as pa
from palaeo_agent import coniss
from palaeo_agent.study import StudySpec, derive

HERE=Path(__file__).resolve().parent
PRIMER='fcc02a57db1ffa2a86d14e7c2540bd7bfa89c14e7e5b3334286f9a24b16747f6'
EXPECTED={'source/neotoma-52767-download.json':'5dd1a71cf7a655f08441e59b866b3eb64c893b164cc8e9320d9ea2d7507ead24',
          'data/counts.tsv':'db922456a78fc78754f8d950066f9032659079808966dcd6de38f2457c6423a6',
          'data/counts-dryland.tsv':'3ab89275221f80b190dbf34b83cc5eebd1f339378b28e402df6b93f8d4d6bfe1',
          'data/counts-final.tsv':'a15f912401a46242a38b48d51211acfb731d70743190cefa27c75474c429d429',
          'data/levels.csv':'806c28064bf275275e8fde15e03fd8a0e5a71b248ab016e16551f71d3376840f'}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path,obj):
    path.write_text(json.dumps(obj,indent=2)+'\n')


def main():
    assert pa.primer()['sha256']==PRIMER
    prior=HERE.parent/'lake-selina'
    assert all(sha(prior/name)==value for name,value in EXPECTED.items())
    request=json.loads((HERE/'extract-spec.json').read_text())
    request['source']=str((HERE/request['source']).resolve())
    extracted=pa.neotoma_extract(request,HERE/'runs-extraction')
    bundle=Path(extracted['bundle'])
    assert pa.inspect_neotoma(bundle)['status']=='verified'
    assert (bundle/'table.tsv').read_bytes()==(prior/'data/counts.tsv').read_bytes()
    (HERE/'data').mkdir(exist_ok=True)
    (HERE/'data/archive.tsv').write_bytes((bundle/'table.tsv').read_bytes())
    (HERE/'data/reconstructed.tsv').write_bytes((prior/'data/counts-final.tsv').read_bytes())
    samples=list(csv.DictReader((bundle/'samples.csv').open()))
    levels=list(csv.DictReader((prior/'data/levels.csv').open()))
    assert [r['sample_id'] for r in samples]==[r['sample_id'] for r in levels]
    assert all(Decimal(a['depth'])==Decimal(b['depth_cm']) for a,b in zip(samples,levels,strict=True))
    with (HERE/'data/positions.csv').open('w',newline='') as stream:
        writer=csv.writer(stream,lineterminator='\n');writer.writerow(['sample_id','depth_cm'])
        writer.writerows((r['sample_id'],r['depth']) for r in samples)
    study=json.loads((HERE/'study.json').read_text()); parsed=StudySpec.model_validate(study)
    raw={name:(HERE/item['path']).read_bytes() for name,item in study['inputs'].items()}
    tables={}; validations={}; preflight=HERE/'runs-preflight';preflight.mkdir(exist_ok=True)
    for name in parsed.datasets:
        files,record=derive(parsed,raw,name)
        for file,data in files.items(): (preflight/file).write_bytes(data)
        tables[name]=list(csv.reader(files[f'{name}.dat'].decode().splitlines(),delimiter='\t'))
        if name=='archive':
            expected=b'.\t'+(prior/'data/counts-dryland.tsv').read_bytes().split(b'\t',1)[1]
            assert files[f'{name}.dat']==expected
    a,b=tables['archive'],tables['repaired']
    assert len(a)==len(b) and a[0]==b[0] and [r[0] for r in a[1:]]==[r[0] for r in b[1:]]
    changes=[{'sample_id':a[i][0],'taxon':a[0][j],'archive':x,'reconstructed':y}
             for i,(ra,rb) in enumerate(zip(a,b,strict=True)) for j,(x,y) in enumerate(zip(ra,rb,strict=True)) if x!=y]
    assert changes==[{'sample_id':'531331','taxon':'Lagarostrobos franklinii','archive':'0','reconstructed':'72'}]
    with patch.object(coniss,'zonation',side_effect=AssertionError('Zonation is forbidden before the freeze')):
        for analysis in study['analyses']:
            dataset=analysis['dataset']
            spec=analysis['spec']|{'input':str(preflight/f'{dataset}.dat'),'metadata':str(preflight/f'{dataset}-metadata.csv')}
            validations[analysis['id']]=pa.validate(spec)
            assert validations[analysis['id']]['status']=='valid'
    for path in ('study.json','plot-study.json'):
        StudySpec.model_validate_json((HERE/path).read_bytes())
    lock={'implementation_commit':'c38696d012fec2fb3a68cba886b13f75a21b3c5f',
          'primer':{k:pa.primer()[k] for k in ('version','sha256')},
          'files':[{'file':name,'sha256':sha(HERE/name)} for name in
                   ('data/archive.tsv','data/reconstructed.tsv','data/positions.csv','study.json','plot-study.json','extract-spec.json','context.json')]}
    write_json(HERE/'input-lock.json',lock)
    write_json(HERE/'intake-check.json',{'extraction_status':'verified','extraction_bundle':str(bundle.relative_to(HERE)),
        'extraction_manifest_sha256':sha(bundle/'manifest.json'),'source_sha256':request['source_sha256'],
        'archive_matches_original':True,'dryland_matches_original':True,'metadata_depths_match_original':True,
        'exact_count_changes':changes,'zonation_guard_active':True,'validations':validations})
    print(json.dumps({'status':'prepared','zonation_computed':False,'validations':validations},indent=2))


if __name__=='__main__':
    main()
