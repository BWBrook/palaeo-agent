import pandas as pd,numpy as np
d=pd.read_csv('shells.tsv',sep='\t',index_col=0,na_values='.')
print(d.describe())
x=d['L1/length'];y=d['L1/width']
print(d[x.isna()^y.isna()])
m=x.notna()&y.notna()
x=x[m];y=y[m]
print(len(x),x.sort_values().tail(3).tolist(),y.sort_values().tail(3).tolist(),x.min(),y.min())
b=np.sign(np.corrcoef(x,y)[0,1])*y.std()/x.std()
print(repr(b),repr(y.mean()-b*x.mean()))
