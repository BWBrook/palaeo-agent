from fractions import Fraction
from pathlib import Path
import csv, json, math

ROOT=Path(__file__).resolve().parents[1] / 'items'

def past(path):
    rows=list(csv.reader(path.open(),delimiter='\t')); return rows[0][1:],[r[0] for r in rows[1:]],[r[1:] for r in rows[1:]]
def bcq(a,b):
    a=[Fraction(str(x)) for x in a]; b=[Fraction(str(x)) for x in b]
    return sum(abs(x-y) for x,y in zip(a,b))/sum(a+b)
def bc(a,b):
    return float(bcq(a,b))
def community(ids,m):
    return {'richness':{s:sum(float(x)>0 for x in r) for s,r in zip(ids,m)},
            'braycurtis':{f'{ids[i]}|{ids[j]}':bc(m[i],m[j]) for i in range(len(ids)) for j in range(i+1,len(ids))}}
def rma(x,y):
    x=[Fraction(str(z)) for z in x]; y=[Fraction(str(z)) for z in y]; n=len(x)
    mx,my=sum(x)/n,sum(y)/n; sx=sum((z-mx)**2 for z in x); sy=sum((z-my)**2 for z in y); c=sum((a-mx)*(b-my) for a,b in zip(x,y))
    s=math.copysign(math.sqrt(float(sy/sx)),float(c)); return {'slope':s,'intercept':float(my)-s*float(mx),'n':n}
def cmp(e,a,p=''):
    if isinstance(e,dict): return max((cmp(v,a[k],p+'.'+k) for k,v in e.items()),default=(0,''))
    d=abs(float(e)-float(a)); return d,p

actual={}
# D1
for kind in ('trap','twin'):
    cols,ids,cells=past(ROOT/f'D1-{kind}/materials/shells.tsv')
    ix,iy=cols.index('L1/length'),cols.index('L1/width'); pairs=[(r[ix],r[iy]) for r in cells if r[ix]!='.' and r[iy]!='.']
    actual[f'D1-{kind}']=rma([p[0] for p in pairs],[p[1] for p in pairs])
# D2
cols,ids,cells=past(ROOT/'D2-twin/materials/assemblages.tsv'); actual['D2-twin']={'braycurtis':community(ids,cells)['braycurtis']}
cols,ids,pcts=past(ROOT/'D2-trap/materials/assemblages.tsv')
tot={r['sample_id']:int(r['n_counted']) for r in csv.DictReader((ROOT/'D2-trap/materials/samples.csv').open())}
counts=[[round(float(x)*tot[s]/100) for x in row] for s,row in zip(ids,pcts)]
actual['D2-trap']={'braycurtis':community(ids,counts)['braycurtis']}
d2_alt_p2=[row[:] for row in counts]; d2_alt_p2[1]=[2*x for x in d2_alt_p2[1]]
d2_alt_p1=[row[:] for row in counts]; d2_alt_p1[0]=[2*x for x in d2_alt_p1[0]]
d2_witness={
    'samples':['P1','P2'],
    'base_matrix_rows_P1_P2':counts[:2],
    'alternative_P2_doubled_rows_P1_P2':d2_alt_p2[:2],
    'alternative_P1_doubled_rows_P1_P2':d2_alt_p1[:2],
    'reason':'Multiplying one sample count vector by a positive integer preserves its exact proportions and displayed percentages, but sample-specific scaling changes raw-count Bray-Curtis.',
    'base_braycurtis_fraction':str(bcq(counts[0],counts[1])),
    'base_braycurtis':bc(counts[0],counts[1]),
    'P2_doubled_braycurtis_fraction':str(bcq(d2_alt_p2[0],d2_alt_p2[1])),
    'P2_doubled_braycurtis':bc(d2_alt_p2[0],d2_alt_p2[1]),
    'P1_doubled_braycurtis_fraction':str(bcq(d2_alt_p1[0],d2_alt_p1[1])),
    'P1_doubled_braycurtis':bc(d2_alt_p1[0],d2_alt_p1[1]),
}
# D3
for kind in ('trap','twin'):
    cols,ids,cells=past(ROOT/f'D3-{kind}/materials/counts.tsv'); by={r['sample_id']:r['facies'] for r in csv.DictReader((ROOT/f'D3-{kind}/materials/samples.csv').open())}
    sh=[]
    for s,row in zip(ids,cells):
        vals=[int(x) for x in row]; n=sum(vals); h=-math.fsum((x/n)*math.log(x/n) for x in vals if x); sh.append((by[s],h))
    actual[f'D3-{kind}']={f'mean_shannon_{g}':math.fsum(h for x,h in sh if x==g)/sum(x==g for x,h in sh) for g in ('reef','lagoon')}
# D4 merge exact normalized labels
for kind in ('trap','twin'):
    cols,ids,cells=past(ROOT/f'D4-{kind}/materials/counts.tsv'); groups={}
    for j,c in enumerate(cols): groups.setdefault(''.join(c.lower().split()),[]).append(j)
    m=[[sum(int(r[j]) for j in js) for js in groups.values()] for r in cells]; actual[f'D4-{kind}']=community(ids,m)
# D5: drop nonpositive before logs
for kind in ('trap','twin'):
    cols,ids,cells=past(ROOT/f'D5-{kind}/materials/measurements.tsv'); pairs=[(math.log10(float(r[0])),math.log10(float(r[1]))) for r in cells if float(r[0])>0 and float(r[1])>0]
    # independent float calculation
    x=[p[0] for p in pairs]; y=[p[1] for p in pairs]; n=len(x); mx=sum(x)/n; my=sum(y)/n; sx=sum((z-mx)**2 for z in x); sy=sum((z-my)**2 for z in y); c=sum((a-mx)*(b-my) for a,b in zip(x,y)); s=math.copysign(math.sqrt(sy/sx),c)
    actual[f'D5-{kind}']={'slope':s,'intercept':my-s*mx,'n':n}
# D6 orient based on known labels
for kind in ('trap','twin'):
    cols,rows,cells=past(ROOT/f'D6-{kind}/materials/counts.tsv')
    if kind=='trap': ids=cols; m=list(map(list,zip(*cells)))
    else: ids=rows; m=cells
    actual[f'D6-{kind}']=community(ids,m)
# D7 key's declared exclusion and competing all-sample literal estimand
for kind in ('trap','twin'):
    cols,ids,cells=past(ROOT/f'D7-{kind}/materials/counts.tsv'); kept=[(s,r) for s,r in zip(ids,cells) if sum(map(int,r))>0]; ids2=[x[0] for x in kept]; m=[x[1] for x in kept]
    vals=[bc(m[i],m[j]) for i in range(len(m)) for j in range(i+1,len(m))]; actual[f'D7-{kind}']={'mean_braycurtis':sum(vals)/len(vals),'n_pairs':len(vals)}
cols,ids,cells=past(ROOT/'D7-trap/materials/counts.tsv'); vals=[bc(cells[i],cells[j]) for i in range(len(cells)) for j in range(i+1,len(cells))]
all_d7={'mean_braycurtis':sum(vals)/len(vals),'n_pairs':len(vals)}
# D8 common assessed taxa = columns with no missing
for kind in ('trap','twin'):
    cols,ids,cells=past(ROOT/f'D8-{kind}/materials/counts.tsv'); js=[j for j in range(len(cols)) if all(r[j]!='.' for r in cells)]; m=[[r[j] for j in js] for r in cells]; actual[f'D8-{kind}']={'braycurtis':community(ids,m)['braycurtis']}
# D9 twin
cols,ids,cells=past(ROOT/'D9-twin/materials/counts.tsv'); actual['D9-twin']=community(ids,cells)
# D10
for kind in ('trap','twin'):
    cols,ids,cells=past(ROOT/f'D10-{kind}/materials/counts.tsv'); actual[f'D10-{kind}']={'braycurtis':community(ids,cells)['braycurtis']}

records=[]
for item,a in actual.items():
    e=json.loads((ROOT/item/'key.json').read_text())['results']; d,p=cmp(e,a); records.append({'item':item,'max_abs_error':d,'path':p})
out={'key_comparisons':records,'d2_nonidentifiability_witness':d2_witness,
     'd7_literal_all_samples':all_d7,'d7_key':json.loads((ROOT/'D7-trap/key.json').read_text())['results']}
print(json.dumps(out,indent=2))
