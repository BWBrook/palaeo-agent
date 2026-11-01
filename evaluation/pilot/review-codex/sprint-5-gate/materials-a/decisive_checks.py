from pathlib import Path
import csv, json, math
from collections import defaultdict
from itertools import combinations

SOURCE = Path('/var/folders/2y/0v0ttwy532n0k7m47vvggdm80000gn/T/palaeo-s5-materials-r2f5bkxz/a')
OUT = Path(__file__).parent

def read(packet, name, delimiter=','):
    with (SOURCE / packet / name).open() as f:
        return list(csv.DictReader(f, delimiter=delimiter))

def matrix(packet):
    rows = read(packet, 'counts.tsv', '\t')
    key = next(iter(rows[0]))
    cols = [x for x in rows[0] if x != key]
    return [r[key] for r in rows], cols, [[float(r[c]) for c in cols] for r in rows]

def bc(x, y):
    return sum(abs(a-b) for a,b in zip(x,y))/(sum(x)+sum(y))

def mean_bc(x):
    return sum(bc(a,b) for a,b in combinations(x,2))/math.comb(len(x),2)

def shannon(x):
    total = sum(x)
    return -sum((a/total)*math.log(a/total) for a in x if a)

def perm_stats(x, groups):
    n=len(x)
    total=sum(bc(x[i],x[j])**2 for i,j in combinations(range(n),2))/n
    within=0
    for g in set(groups):
        idx=[i for i,v in enumerate(groups) if v==g]
        within+=sum(bc(x[i],x[j])**2 for i,j in combinations(idx,2))/len(idx)
    between=total-within
    return {'pseudo_f':(between/(len(set(groups))-1))/(within/(n-len(set(groups)))), 'r_squared':between/total,'n':n}

result={}
for packet in ['079f3c855c','1719318835']:
    ids,cols,x=matrix(packet)
    metadata={r['sample_id']:r for r in read(packet,'samples.csv')}
    recon=[]; audit=[]
    for sid,row in zip(ids,x):
        m=metadata[sid]; n=int(m['n_counted'])
        if m['value_type']=='count':
            recon.append(row); continue
        candidates=[[k for k in range(n+1) if abs(100*k/n-pct)<0.005+1e-10] for pct in row]
        assert all(len(c)==1 for c in candidates)
        values=[c[0] for c in candidates]
        assert sum(values)==n
        recon.append(values)
        audit.append({'sample':sid,'n':n,'all_cells_unique':True,'reconstructed_sum':sum(values),'max_count_rounding_error':max(abs(p*n/100-k) for p,k in zip(row,values))})
    result[packet]={'rounding_assumption':'nearest 0.01 percentage point, denominator n_counted','rows':audit,'mean_bray_curtis_reconstructed':mean_bc(recon),'mean_bray_curtis_mixed_units_invalid':mean_bc(x)}
for packet in ['3a906284d4','8090a86fb2','fddedcbd00']:
    taxa,ids,x=matrix(packet)
    sizes={r['taxon']:r['adult_test_size'] for r in read(packet,'taxa.csv')}
    campaigns={r['core_id']:r['campaign'] for r in read(packet,'cores.csv')}
    samples=list(map(list,zip(*x)))
    retained=[j for j,t in enumerate(taxa) if sizes[t]=='>150 µm']
    result[packet]={}
    for c in sorted(set(campaigns.values())):
        values=[row for sid,row in zip(ids,samples) if campaigns[sid]==c]
        result[packet][c]={'n_cores':len(values),'all_taxa_shannon_mean':sum(map(shannon,values))/len(values),'large_adult_taxa_shannon_mean':sum(shannon([r[j] for j in retained]) for r in values)/len(values)}
    result[packet]['taxa_excluded_by_adult_label']=[t for t in taxa if sizes[t]!='>150 µm']
for packet in ['1f805672ac','79409ec5de']:
    ids,cols,x=matrix(packet)
    register={r['lab_number']:r['core_id'] for r in read(packet,'register.csv')}
    zones={r['core_id']:r['zone'] for r in read(packet,'cores.csv')}
    summed=defaultdict(lambda:[0.0]*len(cols)); normalized=defaultdict(list)
    for sid,row in zip(ids,x):
        core=register[sid]
        summed[core]=[a+b for a,b in zip(summed[core],row)]
        normalized[core].append([a/sum(row) for a in row])
    cores=sorted(summed)
    pool=[[a/sum(summed[c]) for a in summed[c]] for c in cores]
    equal=[[sum(r[j] for r in normalized[c])/len(normalized[c]) for j in range(len(cols))] for c in cores]
    result[packet]={'split_rows':len(ids),'pooled_counts_then_normalized':perm_stats(pool,[zones[c] for c in cores]),'equal_split_proportions_then_averaged_alternative':perm_stats(equal,[zones[c] for c in cores])}
for packet in ['395082bc8f','424e0eca5e']:
    ids,cols,x=matrix(packet)
    stations=read(packet,'stations.csv')
    canonical={r['station_id'].replace('-',''):r for r in stations}
    assert len(canonical)==len(stations)
    assert set(ids)<=set(canonical)
    result[packet]={'matched_counted_samples':len(ids),'uncounted_stations':sorted(set(canonical)-set(ids)),'zone_counts':{z:sum(canonical[s]['zone']==z for s in ids) for z in ['A','B']}}
for packet in ['3748d8955d','4f39decb70','a1323f1f11']:
    ids,cols,x=matrix(packet)
    mapping={r['name_as_recorded']:r['accepted_name'] for r in read(packet,'taxonomy.csv')}
    assert set(cols)==set(mapping)
    merged=sorted(set(mapping.values()))
    y=[[sum(row[j] for j,c in enumerate(cols) if mapping[c]==name) for name in merged] for row in x]
    assert all(sum(a)==sum(b) for a,b in zip(x,y))
    result[packet]={'recorded_columns':len(cols),'accepted_species_observed':sum(any(row[j]>0 for row in y) for j in range(len(merged))),'n_samples':len(ids)}
for packet in ['67e1610024','9d0c6f6d53']:
    taxa,ids,x=matrix(packet)
    samples=list(map(list,zip(*x)))
    result[packet]={'sample_totals':{sid:sum(row) for sid,row in zip(ids,samples)},'n_samples':len(ids)}
(OUT/'decisive_checks.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
