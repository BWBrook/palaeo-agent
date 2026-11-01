import json
import pandas as pd
import palaeo_agent

# Lab numbers are residue splits of the same core, so they are pseudoreplicates;
# the independent sampling unit is the core. Pool counts per core.
c = pd.read_csv('counts.tsv', sep='\t', index_col=0)
reg = pd.read_csv('register.csv')
cores = pd.read_csv('cores.csv')
pooled = c.groupby(reg.set_index('lab_number').loc[c.index, 'core_id']).sum()
pooled.index.name = 'core_id'
pooled.to_csv('pooled_counts.csv')
cores[['core_id', 'zone']].rename(columns={'core_id': 'sample_id'}).to_csv('pooled_meta.csv', index=False)

spec = dict(method='permanova', input='pooled_counts.csv', metadata='pooled_meta.csv',
            group_column='zone', format='delimited', delimiter='comma',
            orientation='samples_by_taxa', value_type='count', distance='braycurtis',
            transform='relative_abundance', missing='error', empty_samples='error',
            design='independent', permutation_scheme='free', permutations=9999, seed=1)
res = palaeo_agent.run(spec, 'runs')
g = res['summary'].get
out = dict(
    status='completed_with_assumptions',
    results=dict(pseudo_f=g('pseudo_f'), r_squared=g('r_squared'), n=g('n'), p_value=g('p_value')),
    assumptions=['Cores (one per site, sites >=3 km apart) are the independent sampling units; free permutation of core labels is valid.',
                 'Splits of one core residue are complementary fractions of one sample, so their counts are summed.'],
    exclusions=[],
    issues=['28 lab numbers come from 14 cores (splits a/b/c of the same residue); treating lab numbers as units would be pseudoreplication, so counts were pooled per core (n=14).',
            'Split totals vary widely (e.g. L4203 has 8 specimens); pooling avoids noisy relative abundances from tiny splits.'],
    summary='Pooled split counts per core, converted to relative abundances, Bray-Curtis, one-way PERMANOVA of inner vs outer zone on 14 cores via palaeo_agent.')
json.dump(out, open('answer.json', 'w'), indent=2)
