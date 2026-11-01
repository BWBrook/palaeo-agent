
import json, numpy as np, pandas as pd
from scipy import stats
rng = np.random.default_rng(20240607)
rows = [l.split() for l in open('dielasma.dat') if l.strip()]
hdr = rows[0][1:]
df = pd.DataFrame([r[1:] for r in rows[1:]], columns=hdr).replace('.', np.nan).astype(float)
res = {'n_rows': len(df)}
D = {}
for L in ['L1','L2','L3']:
    d = df[[L+'/X1', L+'/X2']].dropna(); d.columns = ['len','wid']; D[L] = d
res['n'] = {L: len(d) for L, d in D.items()}
res['anomalies'] = {}
for L, d in D.items():
    res['anomalies'][L] = {'width_gt_length': int((d.wid > d.len).sum()),
        'nonpositive': int((d <= 0).sum().sum()),
        'duplicate_pairs': int(d.duplicated(keep='first').sum())}
# duplicated pairs listing for L2
d2 = D['L2']; dup = d2[d2.duplicated(keep=False)].sort_values(['len','wid'])
res['L2_duplicate_pairs_list'] = [[float(a), float(b), int(c)] for (a,b),c in dup.groupby(['len','wid']).size().items()]

def fit(d, B=2000):
    x, y = np.log(d.len.values), np.log(d.wid.values); n = len(x)
    def slope(x, y):
        r = np.corrcoef(x, y)[0,1]; return np.sign(r)*y.std(ddof=1)/x.std(ddof=1), r
    # width on length: allometry b (wid ~ len^b); RMA slope
    b, r = slope(x, y)
    ols = stats.linregress(x, y)
    bs = []
    for _ in range(B):
        i = rng.integers(0, n, n); bs.append(slope(x[i], y[i])[0])
    lo, hi = np.percentile(bs, [2.5, 97.5])
    a = y.mean() - b*x.mean()
    # linear (untransformed) too
    return {'n': n, 'rma_slope': b, 'rma_ci95_boot': [lo, hi], 'ols_slope': ols.slope,
            'ols_se': ols.stderr, 'ols_ci95': [ols.slope-stats.t.ppf(.975,n-2)*ols.stderr, ols.slope+stats.t.ppf(.975,n-2)*ols.stderr],
            'r': r, 'r2': r*r, 'intercept_rma': a,
            'p_ols_slope_ne_1': 2*stats.t.sf(abs((ols.slope-1)/ols.stderr), n-2),
            'isometry_in_rma_ci': bool(lo <= 1 <= hi)}
res['loglog_fit'] = {L: fit(d) for L, d in D.items()}
allp = pd.concat(D.values()); res['loglog_fit']['pooled'] = fit(allp)
# curvature check: quadratic term in log-log
for L, d in list(D.items()):
    x, y = np.log(d.len), np.log(d.wid); xc = x-x.mean()
    X = np.c_[np.ones(len(x)), xc, xc**2]; beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    s2 = ((y-X@beta)**2).sum()/(len(x)-3); se = np.sqrt(s2*np.linalg.inv(X.T@X)[2,2])
    res['loglog_fit'][L]['quad_coef'] = beta[2]; res['loglog_fit'][L]['quad_p'] = 2*stats.t.sf(abs(beta[2]/se), len(x)-3)
# shape: ratio W/L
res['summary'] = {}
for L, d in D.items():
    ratio = d.wid/d.len
    res['summary'][L] = {'len_mean': d.len.mean(), 'len_median': d.len.median(), 'len_sd': d.len.std(), 'len_min': d.len.min(), 'len_max': d.len.max(),
        'len_skew': stats.skew(d.len), 'len_bimodality_coef': (stats.skew(d.len)**2+1)/(stats.kurtosis(d.len, fisher=False)),
        'wl_mean': ratio.mean(), 'wl_sd': ratio.std()}
res['kruskal_length'] = dict(zip(['H','p'], map(float, stats.kruskal(*[d.len for d in D.values()]))))
res['kruskal_WL'] = dict(zip(['H','p'], map(float, stats.kruskal(*[d.wid/d.len for d in D.values()]))))
pairs = [('L1','L2'),('L1','L3'),('L2','L3')]
res['pairwise'] = {}
for a, b in pairs:
    ra, rb = D[a].wid/D[a].len, D[b].wid/D[b].len
    mw = stats.mannwhitneyu(ra, rb); ks = stats.ks_2samp(D[a].len, D[b].len)
    mwl = stats.mannwhitneyu(D[a].len, D[b].len)
    res['pairwise'][a+'_'+b] = {'WL_MWU_p_bonf3': min(1, 3*mw.pvalue), 'len_MWU_p_bonf3': min(1, 3*mwl.pvalue), 'len_KS_p_bonf3': min(1, 3*ks.pvalue), 'len_KS_D': ks.statistic}
# ANCOVA slope homogeneity and intercept differences (log-log)
def ancova(sets):
    ys = np.concatenate([np.log(D[L].wid) for L in sets]); xs = np.concatenate([np.log(D[L].len) for L in sets])
    g = np.concatenate([[i]*len(D[L]) for i, L in enumerate(sets)]); k = len(sets); n = len(ys)
    def rss(X): b, *_ = np.linalg.lstsq(X, ys, rcond=None); return ((ys-X@b)**2).sum(), X.shape[1]
    G = np.stack([(g==i).astype(float) for i in range(k)], 1)
    r_full, p_full = rss(np.c_[G, G*xs[:,None]]); r_par, p_par = rss(np.c_[G, xs]); r_one, p_one = rss(np.c_[np.ones(n), xs])
    F1 = ((r_par-r_full)/(p_full-p_par))/(r_full/(n-p_full)); F2 = ((r_one-r_par)/(p_par-p_one))/(r_par/(n-p_par))
    return {'slope_homog_F': F1, 'slope_homog_p': stats.f.sf(F1, p_full-p_par, n-p_full),
            'intercept_F': F2, 'intercept_p': stats.f.sf(F2, p_par-p_one, n-p_par)}
res['ancova_all'] = ancova(['L1','L2','L3'])
res['ancova_pairs'] = {a+'_'+b: ancova([a,b]) for a, b in pairs}
# permutation test for centroid (log len, log wid) difference, PERMANOVA-like on Euclid
def perm(sets, P=4999):
    X = np.vstack([np.log(D[L].values) for L in sets]); g = np.concatenate([[i]*len(D[L]) for i, L in enumerate(sets)])
    def F(g):
        gm = X.mean(0); ssb = sum(((g==i).sum())*((X[g==i].mean(0)-gm)**2).sum() for i in range(len(sets)))
        ssw = sum(((X[g==i]-X[g==i].mean(0))**2).sum() for i in range(len(sets))); return (ssb/(len(sets)-1))/(ssw/(len(X)-len(sets)))
    f0 = F(g); c = sum(F(rng.permutation(g)) >= f0 for _ in range(P)); return {'F': f0, 'p': (c+1)/(P+1)}
res['permanova_loglen_logwid'] = perm(['L1','L2','L3'])
# size structure: histogram counts of length, 2-unit bins
bins = np.arange(0, 28, 2)
res['length_hist_bins'] = bins.tolist()
res['length_hist'] = {L: np.histogram(d.len, bins)[0].tolist() for L, d in D.items()}
# Hartigan-like: gap evidence; mixture-by-BIC with 1 vs 2 gaussians on log length
from scipy.stats import norm
def bic_mix(x):
    n = len(x); b1 = -2*norm.logpdf(x, x.mean(), x.std()).sum() + 2*np.log(n)
    best = np.inf
    for s in range(10):
        r = np.random.default_rng(s); m = np.sort(r.choice(x, 2, replace=False)); sd = np.array([x.std()]*2); w = np.array([.5,.5])
        for _ in range(300):
            p = w*norm.pdf(x[:,None], m, sd); p /= p.sum(1, keepdims=True)+1e-300
            w = p.mean(0).clip(1e-3); m = (p*x[:,None]).sum(0)/(p.sum(0)+1e-12); sd = np.sqrt((p*(x[:,None]-m)**2).sum(0)/(p.sum(0)+1e-12)).clip(.03)
        ll = np.log((w*norm.pdf(x[:,None], m, sd)).sum(1)).sum(); best = min(best, -2*ll + 5*np.log(n))
    return b1, best
res['bic_1_vs_2_loglen'] = {L: dict(zip(['bic1','bic2'], map(float, bic_mix(np.log(d.len.values))))) for L, d in D.items()}
# Sensitivity: L2 with duplicated pairs removed (keep first)
d2u = D['L2'].drop_duplicates(); res['L2_dedup_n'] = len(d2u)
Dsave = D['L2']; D['L2'] = d2u
res['L2_dedup_fit'] = fit(d2u); res['L2_dedup_ancova_all'] = ancova(['L1','L2','L3'])
res['L2_dedup_kruskal_length'] = dict(zip(['H','p'], map(float, stats.kruskal(*[d.len for d in D.values()]))))
D['L2'] = Dsave
# Sensitivity: L1 without row 1-? none; leave-out of the 3 smallest/largest not needed.
def clean(o):
    if isinstance(o, dict): return {k: clean(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)): return [clean(v) for v in o]
    if isinstance(o, (np.floating, np.integer)): return o.item()
    return o
json.dump(clean(res), open('results.json','w'), indent=1)
