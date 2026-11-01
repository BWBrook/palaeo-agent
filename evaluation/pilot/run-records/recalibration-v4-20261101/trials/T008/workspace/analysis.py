import json
import numpy as np, pandas as pd
from scipy.spatial.distance import pdist

d = pd.read_csv('dates.csv')
s = pd.read_csv('samples.csv')
c = pd.read_csv('counts.tsv', sep='\t')
acc = d[d.status == 'accepted'].sort_values('depth_cm')
m = s.merge(c, left_on='sample_id', right_on='sample', how='inner')
assert len(m) == len(s) == len(c)
m['age'] = np.interp(m.depth_cm, acc.depth_cm, acc.age_cal_bp)
taxa = [x for x in c.columns if x != 'sample']
h = m[m.age < 11700]
X = h[taxa].values.astype(float)
tot = X.sum(1)
keep = tot > 0
X = X[keep] / tot[keep, None]
bc = pdist(X, 'braycurtis')
res = {'mean_bray_curtis': float(bc.mean()), 'n_holocene': int(len(X))}
out = {
    'status': 'completed_with_assumptions',
    'results': res,
    'assumptions': [
        'Age model: linear interpolation through accepted dates only (rejected date OZ4817 excluded; see exclusions).',
        'Holocene = interpolated age < 11700 cal yr BP (depth approx 222.7 cm).',
        'Bray-Curtis computed on per-sample relative abundances, averaged over all unordered pairs.'],
    'exclusions': [{'id': 'OZ4817', 'reason': 'Radiocarbon date rejected in dating report (age reversal; reworked shell); not used in age model'}]
        + [{'id': r.sample_id, 'reason': 'older than 11700 cal yr BP (not Holocene)'} for r in m[m.age >= 11700].itertuples()],
    'issues': ['Two taxa (Uvigerina peregrina, Textularia agglutinans) have all-zero counts; they do not affect the result.'],
    'summary': 'Joined samples to counts, built age model from accepted dates, selected Holocene samples, converted to relative abundance and averaged pairwise Bray-Curtis.'
}
json.dump(out, open('answer.json', 'w'), indent=2)
