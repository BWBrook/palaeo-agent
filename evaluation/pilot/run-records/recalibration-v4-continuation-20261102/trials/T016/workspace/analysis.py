
import pandas as pd, numpy as np, json
c=pd.read_csv('catalogue.csv');m=pd.read_csv('measurements.csv')
d=c.merge(m,on='specimen_id')
d['lx']=np.log10(d.length_mm);d['ly']=np.log10(d.height_mm)
issues=[]
multi=d[d.individual_id.duplicated(keep=False)]
if d.groupby('individual_id').locality.nunique().max()>1: issues.append('some individuals span localities')
# valves of one animal are not independent: average log values per individual
a=d.groupby('individual_id')[['lx','ly']].mean()
x,y=a.lx.values,a.ly.values
r=np.corrcoef(x,y)[0,1]
slope=np.sign(r)*y.std(ddof=1)/x.std(ddof=1)
icpt=y.mean()-slope*x.mean()
issues.append(f"{len(d)} valve records belong to {len(a)} individuals; {d.individual_id.duplicated().sum()} individuals have two valves (pseudoreplication).")
res=dict(slope=float(slope),intercept=float(icpt),n=int(len(a)))
json.dump(dict(status="completed_with_assumptions",results=res,
assumptions=["Valves of the same individual averaged in log10 space to give one observation per animal","RMA slope = sign(r)*sd(y)/sd(x); log10 of mm values","No outliers removed"],
exclusions=[],issues=issues,
summary="Joined catalogue to measurements, averaged log10 length/height across valves per individual, fitted RMA regression of log10 height on log10 length."),open('answer.json','w'),indent=1)
print(res,issues)
