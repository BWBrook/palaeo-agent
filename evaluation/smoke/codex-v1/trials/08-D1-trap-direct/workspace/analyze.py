import csv,json,math
from pathlib import Path
base=Path.cwd()
with (base/'shells.tsv').open(newline='') as f:
    rows=list(csv.DictReader(f,delimiter='\t'))
pairs=[]
exclusions=[]
for row in rows:
    missing=[k for k in ('L1/length','L1/width') if row[k]=='.']
    if missing:
        exclusions.append({'id':'L1 row '+row['.'],'reason':'Missing '+', '.join(missing)+'; a complete length-width pair is required.'})
    else:
        pairs.append((float(row['L1/length']),float(row['L1/width'])))
n=len(pairs)
xm=math.fsum(x for x,y in pairs)/n
ym=math.fsum(y for x,y in pairs)/n
sxx=math.fsum((x-xm)**2 for x,y in pairs)
syy=math.fsum((y-ym)**2 for x,y in pairs)
sxy=math.fsum((x-xm)*(y-ym) for x,y in pairs)
slope=math.copysign(math.sqrt(syy/sxx),sxy)
intercept=ym-slope*xm
answer={'status':'completed','results':{'slope':slope,'intercept':intercept,'n':n},'assumptions':[],'exclusions':exclusions,'issues':[],'summary':'Fitted reduced major axis regression of untransformed L1 width on length using complete pairs. Slope = sign(covariance) * SD(width)/SD(length); intercept = mean(width) - slope * mean(length). Only locality L1 was analyzed.'}
(base/'answer.json').write_text(json.dumps(answer,indent=2,allow_nan=False)+'\n')
schema=json.loads((base/'answer.schema.json').read_text())
try:
    import jsonschema
except ImportError:
    assert set(answer)==set(schema['required'])
    assert answer['status'] in schema['properties']['status']['enum']
    assert set(answer['results'])=={'slope','intercept','n'}
    assert all(isinstance(answer[k],list) for k in ('assumptions','exclusions','issues'))
    assert isinstance(answer['summary'],str)
    assert all(set(e)=={'id','reason'} and all(isinstance(v,str) for v in e.values()) for e in exclusions)
else:
    jsonschema.validate(answer,schema)
print(json.dumps(answer,indent=2))
