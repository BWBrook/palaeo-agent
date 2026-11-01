import csv
import json
import math
from pathlib import Path
import random
import statistics
import sys
import tempfile

REPO = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(REPO))
from evaluation.pilot.score import score


def csv_rows(path):
    with path.open() as stream:
        return list(csv.DictReader(stream))


def matrix(path, transpose=False):
    with path.open() as stream:
        rows = list(csv.reader(stream, delimiter="\t"))
    labels, taxa = [r[0] for r in rows[1:]], rows[0][1:]
    values = [[float(x) for x in r[1:]] for r in rows[1:]]
    return (taxa, labels, [list(r) for r in zip(*values)]) if transpose else (labels, taxa, values)


def relative(rows):
    return [[v / math.fsum(row) for v in row] for row in rows]


def distances(rows):
    return {(i, j): math.fsum(abs(x-y) for x, y in zip(rows[i], rows[j])) /
            math.fsum(rows[i] + rows[j]) for i in range(len(rows)) for j in range(i)}


def mean_bc(rows):
    return statistics.mean(distances(rows).values())


def permanova(rows, groups):
    d, n = distances(rows), len(rows)
    ss = math.fsum(x*x for x in d.values()) / n
    within = math.fsum(math.fsum(x*x for (i,j), x in d.items() if groups[i] == groups[j] == g) /
                       groups.count(g) for g in set(groups))
    k = len(set(groups))
    return {"pseudo_f": ((ss-within)/(k-1))/(within/(n-k)), "r_squared": (ss-within)/ss, "n": n}


def rma(x, y):
    x, y = [math.log10(v) for v in x], [math.log10(v) for v in y]
    mx, my = statistics.mean(x), statistics.mean(y)
    slope = math.copysign(statistics.stdev(y)/statistics.stdev(x), math.fsum((a-mx)*(b-my) for a,b in zip(x,y)))
    return {"slope": slope, "intercept": my-slope*mx, "n": len(x)}


def shannon(row):
    return -math.fsum(p*math.log(p) for p in relative([row])[0] if p)


def flaw_values(family, m):
    if family in {"P01", "P04", "P11"}:
        ids, names, values = matrix(m/"counts.tsv", True)
    elif family not in {"P07", "P09"}:
        ids, names, values = matrix(m/"counts.tsv")
    if family == "P01":
        dropped = next(r['sample_id'] for r in csv_rows(m/'lab_log.csv') if r['remark'] == 'low yield; counted in full')
        kept = [v for i,v in zip(ids,values) if i != dropped]
        return {'mean_bray_curtis':mean_bc(kept), 'n_samples':len(kept)}
    if family == "P02":
        return permanova(values, [r['zone'] for r in csv_rows(m/'stations.csv')][:len(values)])
    if family == "P03":
        return {'mean_bray_curtis':mean_bc(relative(values))}
    if family == "P04":
        campaigns = {r['core_id']:r['campaign'] for r in csv_rows(m/'cores.csv')}
        return {f'shannon_mean_{c}':statistics.mean(shannon(v) for i,v in zip(ids,values) if campaigns[i] == c)
                for c in ('2017','2021')}
    if family == "P05":
        mapping = {r['name_as_recorded']:r['accepted_name'] for r in csv_rows(m/'taxonomy.csv')}
        targets = [mapping.get(n.split(' (')[0], n.split(' (')[0]) for n in names]
        groups = sorted(set(targets))
        merged = [[sum(v for n,v in zip(targets,row) if n == g) for g in groups] for row in values]
        return {'richness':sum(any(r[j]>0 for r in merged) for j in range(len(groups))), 'mean_bray_curtis':mean_bc(merged)}
    if family == "P06":
        core = {r['lab_number']:r['core_id'] for r in csv_rows(m/'register.csv')}
        zone = {r['core_id']:r['zone'] for r in csv_rows(m/'cores.csv')}
        ids2 = sorted(set(core[i] for i in ids))
        pooled = [[sum(row[j] for i,row in zip(ids,values) if core[i] == c) for j in range(len(names))] for c in ids2]
        return permanova(pooled, [zone[c] for c in ids2])
    if family == "P07":
        rows = csv_rows(m/'shells.csv')
        x = [float(r['length'])*(10 if r['observer']=='AS' else 1) for r in rows]
        y = [float(r['width'])*(10 if r['observer']=='AS' else 1) for r in rows]
        return rma(x,y) | {'mean_length_mm':statistics.mean(x)}
    if family == "P08":
        dates = sorted((float(r['depth_cm']),float(r['age_cal_bp'])) for r in csv_rows(m/'dates.csv') if r['status']=='accepted')
        depths = {r['sample_id']:float(r['depth_cm']) for r in csv_rows(m/'samples.csv')}
        def age(d):
            a,b = next((a,b) for a,b in zip(dates,dates[1:]) if a[0] <= d <= b[0])
            return a[1]+(d-a[0])*(b[1]-a[1])/(b[0]-a[0])
        kept = [v for i,v in zip(ids,values) if age(depths[i]) < 11700]
        return {'mean_bray_curtis':mean_bc(relative(kept)), 'n_holocene':len(kept)}
    if family == "P09":
        cat = {r['specimen_id']:r['individual_id'] for r in csv_rows(m/'catalogue.csv')}
        dropped = sorted(set(cat.values()))[:4]
        rows = [r for r in csv_rows(m/'measurements.csv') if cat[r['specimen_id']] not in dropped]
        return rma([float(r['length_mm']) for r in rows], [float(r['height_mm']) for r in rows])
    if family == "P10":
        depths = {r['sample_id']:float(r['depth_cm']) for r in csv_rows(m/'samples.csv')}
        data = dict(zip(ids,values))
        return {'shannon_change':shannon(data[min(ids,key=depths.get)])-shannon(data[max(ids,key=depths.get)])}
    if family == "P11":
        mapping = {r['name_as_recorded']:r['current_name'].split()[0] for r in csv_rows(m/'taxonomy.csv')}
        targets = [('Globigerina' if mapping[n]=='Globigerinoides' else mapping[n]) for n in names]
        groups = sorted(set(targets))
        merged = [[sum(v for n,v in zip(targets,row) if n == g) for g in groups] for row in values]
        return {'n_genera':sum(any(r[j]>0 for r in merged) for j in range(len(groups))), 'mean_bray_curtis':mean_bc(merged)}
    if family == "P12":
        zones = csv_rows(m/'zonation.csv');depths={r['sample_id']:float(r['depth_cm']) for r in csv_rows(m/'samples.csv')}
        groups = [next(z['zone'] for z in zones if float(z['top_cm']) <= depths[i] < float(z['base_cm'])) for i in ids]
        return permanova(values, groups)


def main():
    checks = []
    for directory in sorted((REPO/'evaluation/pilot/items-v4').glob('*-control')):
        key = json.loads((directory/'key.json').read_text())
        observed = flaw_values(key['family'], directory/'materials')
        target = key['reviewer_flaw']['results']
        error = max(abs(observed[k]-v) for k,v in target.items())
        assert error < 1e-9, (key['item'], observed, target)
        checks.append({'item':key['item'], 'observed':observed, 'max_absolute_error':error})
    choices = []
    for base,label in [('items-v4','P09-trap'),('calibration-v4','P09-cal')]:
        directory=REPO/'evaluation/pilot'/base/label;m=directory/'materials'
        cat={r['specimen_id']:r['individual_id'] for r in csv_rows(m/'catalogue.csv')};groups={}
        for row in csv_rows(m/'measurements.csv'):
            groups.setdefault(cat[row['specimen_id']],[]).append(row)
        for method in ['first_in_measurements','lowest_specimen_id','seeded_0','seeded_1','seeded_2']:
            rng=random.Random(int(method.split('_')[-1])) if method.startswith('seeded') else None
            rows=[rng.choice(g) if rng else g[0] if method=='first_in_measurements' else min(g,key=lambda r:r['specimen_id']) for g in groups.values()]
            results=rma([float(r['length_mm']) for r in rows],[float(r['height_mm']) for r in rows])
            answer={'status':'completed','results':results,'assumptions':['Use one valve per individual, selecting '+method+'.'],
                    'issues':[],'exclusions':[],'summary':'RMA across individuals, not valves.'}
            with tempfile.TemporaryDirectory() as tmp:
                (Path(tmp)/'answer.json').write_text(json.dumps(answer))
                outcome=score(tmp,directory)
            choices.append({'item':label,'rule':method,'answer':answer,'score':outcome})
    print(json.dumps({'independent_flaw_checks':checks,'p09_defensible_choices':choices},indent=2))


if __name__=='__main__':
    main()
