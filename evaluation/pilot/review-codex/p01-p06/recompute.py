"""Materials-only reference computation; never imports toolkit or generated keys."""
import csv
from fractions import Fraction
import hashlib
import itertools
import json
import math
from pathlib import Path
import re

HERE = Path(__file__).resolve().parent
SNAPSHOT = HERE / 'materials-snapshot'


def table(path):
    rows = list(csv.reader(path.open(), delimiter='\t'))
    return rows[0][1:], [r[0] for r in rows[1:]], [
        [None if x == '.' else Fraction(x) for x in r[1:]] for r in rows[1:]]


def metadata(path):
    return list(csv.DictReader(path.open()))


def distances(matrix):
    return [(i, j, sum(abs(a-b) for a,b in zip(matrix[i], matrix[j])) /
            (sum(matrix[i])+sum(matrix[j]))) for i,j in itertools.combinations(range(len(matrix)),2)]


def bcmean(matrix):
    ds = distances(matrix)
    return float(sum(d for i,j,d in ds)/len(ds))


def permanova(matrix, groups):
    ds = distances(matrix)
    n = len(matrix)
    labels = sorted(set(groups))
    total = sum(d*d for i,j,d in ds)/n
    within = sum(sum(d*d for i,j,d in ds if groups[i]==groups[j]==g)/groups.count(g) for g in labels)
    between = total-within
    return {'pseudo_f':float((between/(len(labels)-1))/(within/(n-len(labels)))),
            'r_squared':float(between/total)}


def diversity(matrix, groups):
    hs = [-sum(float(v/sum(row))*math.log(float(v/sum(row))) for v in row if v>0) for row in matrix]
    return {f'shannon_mean_{g}':sum(h for h,k in zip(hs,groups) if k==g)/groups.count(g) for g in sorted(set(groups))}


def compute(item):
    family=int(item.name[1:3]); d=(item/'dictionary.md').read_text()
    result={'status':'completed','results':{},'handling':'','sufficiency':'entailed for requested descriptive statistics',
            'difficulty':'low: explicitly stated data convention; modest numerical work'}
    if family==1:
        columns, rows, x=table(item/'counts.tsv'); x=list(map(list,zip(*x)))
        if 'lost' in d:
            observed=[row for sid,row in zip(columns,x) if sid!='3']
            alternatives={}
            for name,replacement in [('zero_actual_counts',[Fraction(0)]*len(x[0])),
                    ('same_as_core_1',x[0]),('ten_thousand_first_taxon',[Fraction(10000)]+[Fraction(0)]*(len(x[0])-1))]:
                new=[replacement if sid=='3' else row for sid,row in zip(columns,x)]
                alternatives[name]={'mean_bray_curtis':bcmean(new),'n_cores':len(new)}
            result.update(status='stopped',sufficiency='all-core estimand not identifiable; exclusion changes target',
                handling='Core 3 is unobserved, not an observed ecological zero.',
                conditional_results={'mean_bray_curtis':bcmean(observed),'n_cores':len(observed)},
                condition='Restrict the target to the 12 counted cores and disclose exclusion of core 3.',
                nonidentifiability_witness=alternatives)
        else:
            result.update(results={'mean_bray_curtis':bcmean(x),'n_cores':len(x)},handling='Transpose taxa-by-core counts; retain all counted cores.')
    elif family==2:
        columns,rows,x=table(item/'counts.tsv');x=list(map(list,zip(*x)))
        canonical=lambda s: 'LV'+str(int(s[2:]))
        md=metadata(item/'field_log.csv'); mapping={canonical(r['core']):r['zone'] for r in md}
        groups=[mapping[canonical(s)] for s in columns]
        result.update(results=permanova(x,groups),handling='Exact unique match after explicitly stated numeric-code zero-padding normalisation.',
                      assumptions=['An inferential permutation test requires core-level exchangeability/independence, not established by the supplied dictionary. F and R-squared remain calculable.'],
                      incorrect_positional_results=permanova(x,[r['zone'] for r in md]))
    elif family==3:
        columns,rows,x=table(item/'assemblage.tsv')
        md={r['sample']:int(r['n_picked']) for r in metadata(item/'picking.csv')}
        if 'percentages' in d:
            percentages=x
            x=[[v*md[sid]/100 for v in row] for sid,row in zip(rows,x)]
            assert all(v.denominator==1 for row in x for v in row)
            result['incorrect_percentage_results']={'mean_bray_curtis':bcmean(percentages)}
            result['handling']='Reconstruct counts as percentage times known n_picked / 100; all reconstructed counts are integers.'
            result['rounding_check']='Displayed decimal precision and n<=1000 imply an interval of less than or equal to one count per display bin; these exact-centred integer solutions are unique under ordinary nearest rounding.'
        else:result['handling']='Use raw counts as declared; check row totals against picking.csv.'
        assert all(sum(row)==md[sid] for sid,row in zip(rows,x))
        result['results']={'mean_bray_curtis':bcmean(x)}
    elif family==4:
        columns,rows,x=table(item/'counts.tsv')
        md={r['core']:r['campaign'] for r in metadata(item/'cores.csv')};groups=[md[sid] for sid in rows]
        if any(v is None for row in x for v in row):
            common=[j for j in range(len(columns)) if all(row[j] is not None for row in x)]
            common_x=[[row[j] for j in common] for row in x]
            completions={}
            for v in (0,10,1000):
                completed=[[Fraction(v) if a is None else a for a in row] for row in x]
                completions[f'unobserved_each_equals_{v}']=diversity(completed,groups)
            result.update(status='stopped',handling='Unpicked fractions are unknown, not zeros.',
                sufficiency='Full-community 2017 Shannon and common-fraction campaign contrast are not identified.',
                conditional_results=diversity(common_x,groups),
                condition='Change the target explicitly to the eight taxa with recorded counts in every core. This alone does not prove fraction comparability: mainly is not exclusively.',
                nonidentifiability_witness=completions,
                exclusions=[columns[j] for j in range(len(columns)) if j not in common])
        else:result.update(results=diversity(x,groups),handling='Compute each core Shannon using all11 observed taxa, then equally average core indices by campaign.')
    elif family==5:
        columns,rows,x=table(item/'counts.txt');normal=lambda s:' '.join(s.lower().split())
        names=[normal(c) for c in columns];unique=sorted(set(names))
        merged=[[sum(v for v,c in zip(row,names) if c==name) for name in unique] for row in x]
        richness=sum(any(row[j]>0 for row in merged) for j in range(len(unique)))
        result.update(results={'richness':richness,'mean_bray_curtis':bcmean(merged)},
            handling='Normalise capitalization/whitespace only, merge identical binomial count columns by sum.',
            incorrect_unmerged_results={'richness':len(columns),'mean_bray_curtis':bcmean(x)})
    elif family==6:
        columns,rows,x=table(item/'counts.tsv');md={r['sample']:r['zone'] for r in metadata(item/'zones.csv')}
        if 'aliquots' in d:
            units=[re.sub('[abc]$','',sid) for sid in rows];unique=sorted(set(units))
            pooled=[[sum(row[j] for row,unit in zip(x,units) if unit==u) for j in range(len(columns))] for u in unique]
            groups=[]
            for u in unique:
                gs={md[sid] for sid,unit in zip(rows,units) if unit==u};assert len(gs)==1;groups.append(gs.pop())
            result['incorrect_aliquot_results']={**permanova([[v/sum(row) for v in row] for row in x],[md[s] for s in rows]),'n':len(x)}
            x=pooled
            result['handling']='Pool equal-picked aliquots by core (sum then relative abundance); cores are replication units.'
            result['sufficiency']='Core unit is entailed. Pooling all equal-size aliquots is a natural lossless summary; literal 999 distinct permutations impossible for six cores, but repeated Monte Carlo draws are possible.'
        else:
            groups=[md[s] for s in rows];result['handling']='Each row is a separate randomly located core; use its relative abundance.'
        x=[[v/sum(row) for v in row] for row in x]
        result['results']={**permanova(x,groups),'n':len(x)}
    return result


if __name__=='__main__':
    predictions={}
    manifest={}
    for section in ('items','calibration'):
        for item in sorted((SNAPSHOT/section).iterdir()):
            for file in sorted(item.iterdir()):
                manifest[str(file.relative_to(SNAPSHOT))]=hashlib.sha256(file.read_bytes()).hexdigest()
            predictions[f'{section}/{item.name}']=compute(item)
    output={'baseline_commit':'71f29d1','bank_commit':'4bf28f8','independence':'Only material snapshots read; stdlib Fraction/statistical formulas; no key, generator or toolkit code read/imported.',
            'material_sha256':manifest,'predictions':predictions}
    with (HERE/'predictions.json').open('x') as f:json.dump(output,f,indent=2,allow_nan=False);f.write('\n')
    seal={'prediction_sha256':hashlib.sha256((HERE/'predictions.json').read_bytes()).hexdigest(),
          'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'keys_read_before_seal':False,'n_items':len(predictions)}
    with (HERE/'seal.json').open('x') as f:json.dump(seal,f,indent=2);f.write('\n')
    print(json.dumps(seal))
