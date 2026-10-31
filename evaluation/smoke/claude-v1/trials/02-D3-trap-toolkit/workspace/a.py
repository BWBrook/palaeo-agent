import pandas as pd,numpy as np
c=pd.read_csv('counts.tsv',sep='\t',index_col=0);s=pd.read_csv('samples.csv').set_index('sample_id')
print(c.isna().sum().sum(),c.sum(1).to_dict(),set(c.index)^set(s.index))
p=c.div(c.sum(1),axis=0)
H=-(p*np.log(p.where(p>0))).sum(1)
print(H);print(repr(H.groupby(s.facies).mean().to_dict()))
