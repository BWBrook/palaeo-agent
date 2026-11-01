
import numpy as np, pandas as pd, json
rng = np.random.default_rng(20240607)
rows = [l.split() for l in open('llanvirn.dat') if l.strip()]
hz = [int(x) for x in rows[0][1:]]
tax = [r[0][3:] for r in rows[1:]]          # drop undocumented _N_ code
X = pd.DataFrame([[int(v) for v in r[1:]] for r in rows[1:]], index=tax, columns=hz)
N = X.sum(); S = (X>0).sum()
out = {'n_taxa': len(tax), 'totals': N.to_dict(), 'richness': S.to_dict(),
       'singletons': (X==1).sum().to_dict()}
P = X/N
out['prop_Sowerbyella'] = P.loc['Sower'].round(4).to_dict()
out['prop_Basil'] = P.loc['Basil'].round(4).to_dict()
out['prop_nonSower_nonBasil'] = (1-P.loc['Sower']-P.loc['Basil']).round(4).to_dict()
# Simpson / Shannon
def shannon(c):
    p=c[c>0]/c.sum(); return float(-(p*np.log(p)).sum())
def invsimp(c):
    p=c/c.sum(); return float(1/(p**2).sum())
out['shannon']={h:shannon(X[h].values) for h in hz}
out['inv_simpson']={h:invsimp(X[h].values) for h in hz}
# rarefaction expected richness at common n (smallest total) and analytic
from scipy.special import gammaln
def rare(c,n):
    c=c[c>0]; T=c.sum()
    lg=lambda a,b: gammaln(a+1)-gammaln(b+1)-gammaln(a-b+1)
    return float(sum(1-np.exp(lg(T-k,n)-lg(T,n)) if T-k>=n else 1 for k in c))
nmin=int(N.min()); out['rarefy_n']=nmin
out['rarefied_richness']={h:rare(X[h].values,nmin) for h in hz}
out['rarefied_richness_n50']={h:rare(X[h].values,50) for h in hz if N[h]>=50}
# representations
reps = {'proportion':P, 'sqrt_prop':np.sqrt(P), 'presence':(X>0).astype(float),
        'log_count':np.log1p(X), 'prop_no_Sower':(X.drop('Sower')/X.drop('Sower').sum())}
def bc(a,b): return float(np.abs(a-b).sum()/(a+b).sum())
pairs=[(i,i+1) for i in range(1,10)]
out['bray_curtis']={}
for k,R in reps.items():
    out['bray_curtis'][k]={f'{a}-{b}':bc(R[a].values,R[b].values) for a,b in pairs}
# bootstrap uncertainty of BC (multinomial resampling of counts) for proportion & presence
def boot(a,b,kind,B=2000):
    pa=X[a].values/N[a]; pb=X[b].values/N[b]; r=[]
    for _ in range(B):
        ca=rng.multinomial(N[a],pa); cb=rng.multinomial(N[b],pb)
        if kind=='prop': r.append(bc(ca/ca.sum(),cb/cb.sum()))
        else: r.append(bc((ca>0)*1.,(cb>0)*1.))
    return [float(np.percentile(r,2.5)),float(np.median(r)),float(np.percentile(r,97.5))]
out['bc_boot_CI']={k:{f'{a}-{b}':boot(a,b,k) for a,b in pairs} for k in ['prop','presence']}
# null expectation: BC between two samples of same pooled composition at the same totals
def nullbc(a,b,B=2000):
    pool=(X[a]+X[b]).values; p=pool/pool.sum(); r=[]
    for _ in range(B):
        ca=rng.multinomial(N[a],p); cb=rng.multinomial(N[b],p); r.append(bc(ca/ca.sum(),cb/cb.sum()))
    obs=bc(P[a].values,P[b].values)
    return {'obs':obs,'null_median':float(np.median(r)),'null_95':float(np.percentile(r,95)),'p':float((np.sum(np.array(r)>=obs)+1)/(B+1))}
out['null_homogeneity']={f'{a}-{b}':nullbc(a,b) for a,b in pairs}
# Sowerbyella proportion CIs (Wilson) and ratio changes
def wilson(k,n,z=1.96):
    p=k/n; d=1+z*z/n; c=p+z*z/(2*n); h=z*np.sqrt(p*(1-p)/n+z*z/(4*n*n))
    return [float((c-h)/d),float((c+h)/d)]
out['wilson_Sower']={h:wilson(X.loc['Sower',h],N[h]) for h in hz}
out['wilson_Basil']={h:wilson(X.loc['Basil',h],N[h]) for h in hz}
# per-taxon change 5->6 and 6->7 : proportions & Fisher exact
from scipy.stats import fisher_exact
for a,b in [(5,6),(6,7)]:
    t={}
    for g in tax:
        if X.loc[g,[a,b]].sum()==0: continue
        tab=[[X.loc[g,a],N[a]-X.loc[g,a]],[X.loc[g,b],N[b]-X.loc[g,b]]]
        p=fisher_exact(tab)[1]
        t[g]={'count_a':int(X.loc[g,a]),'count_b':int(X.loc[g,b]),'prop_a':float(P.loc[g,a]),'prop_b':float(P.loc[g,b]),'fisher_p':float(p),'p_holm_like_bonf':float(min(1,p*len(X)))}
    out[f'taxon_change_{a}_{b}']=t
# 6 vs 7 excluding Sower and Basil (is "rest of fauna" changing?)
for a,b in [(5,6),(6,7)]:
    sub=X.drop(['Sower','Basil'])
    out[f'rest_fauna_{a}_{b}']={'n_a':int(sub[a].sum()),'n_b':int(sub[b].sum()),
      'bc_prop':bc((sub[a]/sub[a].sum()).values,(sub[b]/sub[b].sum()).values)}
# rank order of horizon totals and correlation of total with richness
from scipy.stats import spearmanr
out['spearman_total_vs_richness']=float(spearmanr(N,S)[0])
out['spearman_total_vs_richness_p']=float(spearmanr(N,S)[1])
# Unconformity split: mean BC within/between members
UF=[1,2,3,4,5,6]; AL=[7,8,9,10]
out['mean_pooled_prop']={'UFG':(X[UF].sum()/X[UF].sum().sum()).round(4).to_dict(),'AL':(X[AL].sum()/X[AL].sum().sum()).round(4).to_dict()}
# ordination (PCoA of BC on sqrt prop) axis 1 scores
D=np.array([[bc(reps['sqrt_prop'][i].values,reps['sqrt_prop'][j].values) for j in hz] for i in hz])
n=len(hz); J=np.eye(n)-1/n; B_=-0.5*J@(D**2)@J; w,v=np.linalg.eigh(B_); idx=np.argsort(w)[::-1]
out['pcoa_sqrt_bc']={'eig_frac':(w[idx][:2]/w[w>0].sum()).tolist(),'axis1':dict(zip(hz,(v[:,idx[0]]*np.sqrt(w[idx[0]])).tolist())),'axis2':dict(zip(hz,(v[:,idx[1]]*np.sqrt(w[idx[1]])).tolist()))}
json.dump(out,open('results.json','w'),indent=1,default=float)
