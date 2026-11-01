import json
from pathlib import Path
import tempfile
from palaeo_agent import run_study, inspect_study, reproduce_study
from palaeo_agent.community import calculate_community
from palaeo_agent.mcp_server import Transport, tool_definitions

BASE = {'method':'community','input':'x','format':'delimited','delimiter':'comma','orientation':'samples_by_taxa','value_type':'count','transform':'none','distance':'braycurtis','dimensions':1,'missing':'error','empty_samples':'error'}
def calculate(text):
    try:
        x=calculate_community(BASE,text.encode())
        return {'status':'accepted','sample_ids':x['sample_ids'],'taxon_ids':x['taxon_ids'],'counts':x['retained_counts']}
    except Exception as e:
        return {'status':'error','type':type(e).__name__,'code':getattr(e,'code',None),'message':str(e)}

out={}
out['literal_NA_id']=calculate('sample,A,B\nNA,1,2\nS2,3,5\nS3,6,1\n')
out['blank_row_id']=calculate('sample,A,B\n,1,2\nS2,3,5\nS3,6,1\n')
out['blank_taxon_id']=calculate('sample,,B\nS1,1,2\nS2,3,5\nS3,6,1\n')
out['literal_NA_taxon']=calculate('sample,NA,B\nS1,1,2\nS2,3,5\nS3,6,1\n')
out['unclosed_numeric_quote']=calculate('sample,A,B\nS1,1,2\nS2,3,5\nS3,6,"1')
out['explicit_all_missing_row']=calculate('sample,A,B\nS1,1,2\n,,\nS2,3,5\nS3,6,1\n')
out['spaced_sample_id']=calculate('sample,A,B\n" S1 ",1,2\nS2,3,5\nS3,6,1\n')
with tempfile.TemporaryDirectory(prefix='s5-toolkit-') as temp:
    root=Path(temp)
    (root/'counts.csv').write_text('sample,"Taxon, alpha",Taxon beta\nS1,1,2\nS2,3,5\nS3,6,1\n')
    study={'study_version':1,'inputs':{'c':{'kind':'counts','path':'counts.csv','format':'delimited','delimiter':'comma','orientation':'samples_by_taxa'}},'datasets':{'d':{'source':'c'}},'analyses':[{'id':'a','dataset':'d','spec':{k:v for k,v in (BASE|{'format':'past'}).items() if k not in ('input','delimiter')}}]}
    x=run_study(study,root/'study',base_dir=root)
    v=inspect_study(x['study_dir'])
    out['quoted_comma_study']={'status':x['status'],'reproduction':reproduce_study(x['study_dir'],root/'again')['status'],'derived':(root/'study/derived/d.dat').read_text()}
    (root/'shells.csv').write_text('sample,Shell length,Shell width\nS1,10,5\nS2,20,12\nS3,30,20\n')
    m={'study_version':1,'inputs':{'c':{'kind':'measurements','path':'shells.csv','format':'delimited','delimiter':'comma','orientation':'samples_by_taxa'}},'datasets':{'d':{'source':'c'}},'analyses':[{'id':'a','dataset':'d','spec':{'method':'rma','format':'past','x':'Shell length','y':'Shell width','transform':'none','missing':'error'}}]}
    x=run_study(m,root/'measure',base_dir=root)
    out['spaced_measurement_study']=x
    definitions=tool_definitions()
    refs=[]
    def visit(value,root_schema):
        if isinstance(value,dict):
            if '$ref' in value:
                ref=value['$ref']; node=root_schema
                try:
                    for part in ref.removeprefix('#/').split('/'): node=node[part]
                except KeyError:refs.append(ref)
            for v in value.values():visit(v,root_schema)
        elif isinstance(value,list):
            for v in value:visit(v,root_schema)
    for d in definitions:visit(d['inputSchema'],d['inputSchema'])
    out['schema']={'unresolved_refs':refs,'invalid_request':Transport(root).dispatch('validate',{'spec':{'method':'community','input':'counts.csv'}}),'capabilities':Transport(root).dispatch('discover',{})}
print(json.dumps(out,indent=2))
