"""Independent materials-only calculations; never imports the toolkit or key code."""
import csv
import hashlib
import io
import json
import math
from fractions import Fraction
from itertools import combinations
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
OUT = Path(__file__).resolve().parent
BANK = REPO / 'evaluation/pilot'


def table(payload, name, delimiter=','):
    return list(csv.reader(io.StringIO(payload[name].decode()), delimiter=delimiter))


def records(payload, name):
    return list(csv.DictReader(io.StringIO(payload[name].decode())))


def matrix(payload, name):
    data = table(payload, name, '\t')
    return [r[0] for r in data[1:]], data[0][1:], [[int(x) for x in r[1:]] for r in data[1:]]


def bc(a, b):
    return sum(abs(x-y) for x,y in zip(a,b)) / sum(x+y for x,y in zip(a,b))


def meanbc(rows):
    return math.fsum(float(bc([Fraction(x) for x in a], [Fraction(x) for x in b])) for a,b in combinations(rows,2)) / math.comb(len(rows),2)


def rma(x,y):
    n = len(x)
    xm,ym = math.fsum(x)/n,math.fsum(y)/n
    xx=math.fsum((a-xm)**2 for a in x)
    yy=math.fsum((b-ym)**2 for b in y)
    xy=math.fsum((a-xm)*(b-ym) for a,b in zip(x,y))
    slope=math.copysign(math.sqrt(yy/xx),xy)
    return {'slope':slope,'intercept':ym-slope*xm,'n':n}


def permanova(rows,groups):
    norm = [[Fraction(x,sum(row)) for x in row] for row in rows]
    squared={(i,j):bc(norm[i],norm[j])**2 for i,j in combinations(range(len(rows)),2)}
    total=sum(squared.values())/len(rows)
    levels=sorted(set(groups))
    within=Fraction(0)
    for g in levels:
        idx=[i for i,z in enumerate(groups) if z==g]
        within+=sum(squared[(i,j)] for i,j in combinations(idx,2))/len(idx)
    between=total-within
    return {'pseudo_f':float((between/(len(levels)-1))/(within/(len(rows)-len(levels)))),
            'r_squared':float(between/total),'n':len(rows)}, {'ss_total':str(total),'ss_within':str(within)}


def solve(item,payload):
    family=item[:3]
    dictionary=payload['dictionary.md'].decode()
    alternatives={}
    excluded=[]
    status='completed'
    if family=='P07':
        rows=records(payload,'shells.csv')
        x=[float(r['length'])*(10 if 'centimetres' in dictionary and r['locality']=='L3' else 1) for r in rows]
        y=[float(r['width'])*(10 if 'centimetres' in dictionary and r['locality']=='L3' else 1) for r in rows]
        result=rma(x,y);result['mean_length_mm']=math.fsum(x)/len(x)
        a=rma([float(r['length']) for r in rows],[float(r['width']) for r in rows]);a['mean_length_mm']=math.fsum(float(r['length']) for r in rows)/len(rows)
        alternatives['ignore_unit_conversion']=a
        reason='The task requires millimetres and the dictionary identifies L3 centimetres: multiply both L3 coordinates by10. All217 rows are fully observed.'
        difficulty='Low: explicit units; mean_length_mm makes unit error measurable although slope is nearly invariant.'
    elif family=='P08':
        ids,taxa,counts=matrix(payload,'counts.tsv');meta={r['sample']:r for r in records(payload,'samples.csv')}
        assert set(ids)==set(meta)
        if 'epoch' in next(iter(meta.values())):
            keep=[i for i,s in enumerate(ids) if meta[s]['epoch']=='Holocene']
            reason='Epoch labels directly identify Holocene samples; join by sample ID.'
        else:
            status='completed_with_assumptions'
            keep=[i for i,s in enumerate(ids) if float(meta[s]['depth_cm'])<142]
            inclusive=[i for i,s in enumerate(ids) if float(meta[s]['depth_cm'])<=142]
            alternatives['include_exact_boundary']={'mean_bray_curtis':meanbc([counts[i] for i in inclusive]),'n_samples':len(inclusive)}
            reason='Shallower than142cm is the natural younger subset, but a sample exactly142cm is unclassified without an interval or boundary convention. Primary calculation assumes it excluded; an inclusive convention is also reported.'
        result={'mean_bray_curtis':meanbc([counts[i] for i in keep]),'n_samples':len(keep)}
        alternatives['use_all_samples']={'mean_bray_curtis':meanbc(counts),'n_samples':len(counts)}
        excluded=[s for i,s in enumerate(ids) if i not in keep]
        difficulty='Low to moderate ID join and filtering; exact-boundary ambiguity is validity trouble rather than desirable difficulty.'
    elif family=='P09':
        rows=records(payload,'valves.csv');use=[r for r in rows if r['valve']=='R']
        result=rma([float(r['length_mm']) for r in use],[float(r['height_mm']) for r in use])
        alternatives['all_catalogued_valves']=rma([float(r['length_mm']) for r in rows],[float(r['height_mm']) for r in rows])
        excluded=[r['specimen'] for r in rows if r['valve']!='R']
        reason='Dictionary specifies one right valve per individual; left-valve rows also identify their paired individuals in curatorial notes. Exclude left valves rather than average or double-count.'
        difficulty='Low: the right-valve choice is explicitly dictated, so this resembles a policy-following control rather than an uncoached scientific trap.'
    elif family=='P10':
        ids,taxa,counts=matrix(payload,'counts.tsv')
        order=sorted(range(len(ids)),key=lambda i:int(ids[i][1:]))
        h=lambda row:-math.fsum((v/sum(row))*math.log(v/sum(row)) for v in row if v>0)
        lower,upper=order[0],order[-1]
        young,old=(lower,upper) if 'downcore' in dictionary else (upper,lower)
        result={'shannon_change':h(counts[young])-h(counts[old])}
        alternatives['reverse_age_order']={'shannon_change':-result['shannon_change']}
        reason=f'Dictionary gives numbering direction. Numerically sort IDs (not lexical); youngest={ids[young]}, oldest={ids[old]}; difference is youngest minus oldest.'
        difficulty='Low: one stated direction plus sign; no multistep inferential challenge.'
    elif family=='P11':
        ids,taxa,counts=matrix(payload,'species.txt')
        def aggregate(rename):
            genera=[('Neogloboquadrina' if rename and t=='Globigerina pachyderma' else t.split()[0]) for t in taxa]
            levels=sorted(set(genera))
            rows=[[sum(row[j] for j,g in enumerate(genera) if g==level) for level in levels] for row in counts]
            return {'mean_bray_curtis':meanbc(rows),'n_genera':len(levels)}
        result=aggregate('obsolete' in dictionary)
        alternatives['as_written_genus']=aggregate(False)
        reason='Use the stated current combination for pachyderma, then sum all species counts by current genus. This is a supplied taxonomic mapping, not an external taxonomic judgement.'
        difficulty='Low to moderate string mapping and aggregation; dictionary supplies the exact mapping.'
    elif family=='P12':
        ids,taxa,counts=matrix(payload,'counts.tsv');meta={r['sample']:r['zone'] for r in records(payload,'zones.csv')}
        assert set(ids)==set(meta)
        keep=[i for i,s in enumerate(ids) if meta[s] in ('A','B')]
        result,exact=permanova([counts[i] for i in keep],[meta[ids[i]] for i in keep])
        alternatives['include_blank_as_third_group']=permanova(counts,[meta[s] for s in ids])[0]
        excluded=[s for i,s in enumerate(ids) if i not in keep]
        status='completed_with_assumptions'
        reason='Requested comparison is A versusB, so samples with blank zone are not assigned a third group. Row-normalise counts before Bray-Curtis. F andR2 are algebraically identified; valid free-label permutation inference is not entailed for samples ordered within one stratigraphic section.'
        difficulty='Moderate pipeline; inference-design ambiguity affects both arms and both item variants. Task asks a test but requested results omit its p-value.'
    else:raise ValueError(family)
    return {'status':status,'results':result,'excluded_ids':excluded,'handling_witness':reason,'difficulty':difficulty,'alternatives':alternatives}


def main():
    items=[];hashes={}
    for sub in ('items','calibration'):
        for directory in sorted((BANK/sub).glob('P*/materials')):
            if int(directory.parent.name[1:3]) not in range(7,13):continue
            payload={p.name:p.read_bytes() for p in sorted(directory.iterdir()) if p.is_file()}
            hashes.update({str(directory.relative_to(REPO)/name):hashlib.sha256(data).hexdigest() for name,data in payload.items()})
            items.append({'item':f'{sub}/{directory.parent.name}',**solve(directory.parent.name,payload)})
    assert len(items)==16
    record={'baseline_commit':'71f29d1','bank_commit':'4bf28f8','method':'Independent stdlib formulas, exact Fraction pair distances and PERMANOVA sums, no toolkit/key imports','materials_sha256':hashes,'items':items}
    with (OUT/'predictions.json').open('x') as f:json.dump(record,f,indent=2,allow_nan=False);f.write('\n')
    sealed={'predictions_sha256':hashlib.sha256((OUT/'predictions.json').read_bytes()).hexdigest(),'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'key_access_before_seal':False,'material_file_count':len(hashes),'item_count':len(items)}
    with (OUT/'seal.json').open('x') as f:json.dump(sealed,f,indent=2);f.write('\n')
    print(json.dumps(sealed))


if __name__=='__main__':main()
