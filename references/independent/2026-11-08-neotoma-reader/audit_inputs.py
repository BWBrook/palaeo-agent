import copy,csv,hashlib,io,json,sys
from pathlib import Path
import palaeo_agent as pa
D=Path(sys.argv[1]).resolve()
D.mkdir(parents=True,exist_ok=False)
def datum(label,value,units='NISP',group='TRSH',taxon=1):return {'variablename':label,'value':value,'units':units,'element':'pollen','ecologicalgroup':group,'taxonid':taxon,'elementtype':'pollen','taxongroup':'Vascular plants'}
def sample(sid,depth,data,ages=None):return {'sampleid':sid,'depth':depth,'datum':data,'ages':ages or []}
def record(dsid,siteid,name,samples):return {'site':{'siteid':siteid,'sitename':name,'geography':json.dumps({'type':'Point','coordinates':[146.5,-42.1]}),'altitude':None,'collectionunit':{'collectionunitid':siteid*10,'notes':'line1,\nÅ line2','defaultchronology':7,'dataset':{'datasetid':dsid,'datasetname':'D, '+str(dsid),'doi':['doi1',{'z':2,'a':1}],'datasetpi':[{'z':'PI, Å','a':None}],'samples':samples}}}}
def baseline():return {'data':[record(1,10,'Alpha',[sample(10,20,[datum('Pinus',5),datum('Poaceae',3,group='UPHE',taxon=2)],[{'chronologyid':7,'chronologyname':'C, Å','agetype':'cal BP','age':100,'ageolder':None,'ageyounger':90},{'chronologyid':8,'age':110}]),sample(11,10,[datum('Pinus',2)]),sample(12,30,[])]),record(2,20,'Beta',[sample(20,0,[datum('Poaceae',7,group='UPHE',taxon=2)])]),record(3,30,'Gamma',[sample(30,0,[datum('Pinus',1.5,units='percent')])])]}
def datasets(doc):return [r['site']['collectionunit']['dataset'] for r in doc['data']]
def kept(doc):return [v for ds in datasets(doc)[:2] for s in ds['samples'] for v in s['datum']]
def first(doc):return datasets(doc)[0]['samples'][0]['datum'][0]
def samples1(doc):return datasets(doc)[0]['samples']
results=[]
def probe(name,mutator=lambda d:None,changes=None,literal=None):
 doc=baseline();mutator(doc);raw=json.dumps(doc,ensure_ascii=False).encode()
 if literal:raw=raw.replace(b'"REPLACE_LITERAL"',literal.encode())
 p=D/(name+'.json');p.write_bytes(raw);spec=dict(source=str(p),source_sha256=hashlib.sha256(raw).hexdigest(),datasets=[1,2],units='NISP',elements=['pollen'],ecological_groups=['TRSH','UPHE'],absent_taxa='zero',row_order='source');spec.update(changes or {})
 item={'case':name,'source':str(p),'spec':spec}
 try:
  out=pa.neotoma_extract(spec,D/'bundles');b=Path(out['bundle']);item.update(status='complete',bundle=str(b),table=(b/'table.tsv').read_text(),taxa=list(csv.DictReader((b/'taxa.csv').open())),samples=list(csv.DictReader((b/'samples.csv').open())),ages=list(csv.DictReader((b/'ages.csv').open())),extract=json.loads((b/'extract.json').read_text()))
  try:
   valid=pa.validate(dict(method='community',input=str(b/'table.tsv'),format='delimited',delimiter='tab',orientation='samples_by_taxa',value_type='abundance' if out['kind']=='abundance' else 'count',transform='none',distance='braycurtis',dimensions=1,missing='error',empty_samples='drop'));item['downstream_validation']=valid
  except Exception as e:item['downstream_validation']={'type':type(e).__name__,'code':getattr(e,'code',None),'message':str(e)}
  if name in ('quoted_label','percent_underflow') and item['downstream_validation'].get('status') == 'valid':
   analysis_spec=dict(method='community',input=str(b/'table.tsv'),format='delimited',delimiter='tab',orientation='samples_by_taxa',value_type='abundance' if out['kind']=='abundance' else 'count',transform='none',distance='braycurtis',dimensions=1,missing='error',empty_samples='drop')
   analysis=pa.run(analysis_spec,D/'analyses');result=pa.inspect_run(analysis['run_dir'])['result']
   item['parsed_taxon_ids']=result['taxon_ids'];item['diversity']=result['diversity']
 except Exception as e:item.update(status='raised',type=type(e).__name__,code=getattr(e,'code',None),message=str(e))
 results.append(item)
probe('baseline')
probe('all_mixed_units',changes={'datasets':'all'})
probe('unknown_dataset',changes={'datasets':[1,99]})
probe('duplicate_sample',lambda d:datasets(d)[1]['samples'][0].update(sampleid=10))
probe('repeated_label',lambda d:samples1(d)[0]['datum'].append(datum('Pinus',2)))
probe('label_collision',lambda d:samples1(d)[1]['datum'][0].update(taxonid=99))
probe('wrong_data_shape',lambda d:d.update(data={}))
probe('wrong_ages_shape',lambda d:samples1(d)[0].update(ages=None))
probe('wrong_element_type',lambda d:first(d).update(element=[]))
probe('wrong_group_type',lambda d:first(d).update(ecologicalgroup={}))
probe('wrong_taxonid_type',lambda d:[v.update(taxonid={'bad':1}) for v in kept(d) if v['variablename']=='Pinus'])
probe('tab_label',lambda d:[v.update(variablename='Pi\tnus') for v in kept(d) if v['variablename']=='Pinus'])
probe('newline_label',lambda d:[v.update(variablename='Pi\nnus') for v in kept(d) if v['variablename']=='Pinus'])
probe('quoted_label',lambda d:[v.update(variablename='"Pinus"') for v in kept(d) if v['variablename']=='Pinus'])
probe('age_duplicate',lambda d:samples1(d)[0]['ages'].append({'chronologyid':7,'age':1}))
probe('depth_order',changes={'row_order':'depth'})
probe('depth_tie',lambda d:samples1(d)[0].update(depth=10),changes={'row_order':'depth'})
probe('depth_infinite',lambda d:samples1(d)[0].update(depth='REPLACE_LITERAL'),changes={'row_order':'depth'},literal='1e400')
def percent(doc):
 for v in kept(doc):v['units']='percent'
 first(doc)['value']='REPLACE_LITERAL'
probe('percent_underflow',percent,changes={'units':'percent'},literal='1e-400')
probe('percent_huge_integer',percent,changes={'units':'percent'},literal='1'+'0'*400)
(D/'receipts.json').write_text(json.dumps({'commit':'6f17b50','primer':{k:v for k,v in pa.primer().items() if k!='text'},'probes':results},indent=2,ensure_ascii=False))
for r in results:print(json.dumps({k:r[k] for k in ['case','status','type','code','message','downstream_validation'] if k in r}))
