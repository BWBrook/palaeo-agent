"""Materials-only recomputation of frozen flaw values; no bank/toolkit imports."""
import csv
from fractions import Fraction
import hashlib
from itertools import combinations
import json
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
ITEMS = ROOT / "evaluation/pilot/items"


def table(item, name="counts.tsv", transpose=False):
    rows = list(csv.reader((ITEMS/item/"materials"/name).open(), delimiter="\t"))
    names, ids = rows[0][1:], [r[0] for r in rows[1:]]
    data = [[Fraction(v) for v in r[1:]] for r in rows[1:]]
    return (ids, names, list(map(list, zip(*data)))) if transpose else (names, ids, data)


def meta(item, name):
    return list(csv.DictReader((ITEMS/item/"materials"/name).open()))


def relative(data):
    return [[v/sum(row) for v in row] for row in data]


def bc(a, b):
    return sum(abs(x-y) for x, y in zip(a,b))/(sum(a)+sum(b))


def meanbc(data):
    d = [bc(a,b) for a,b in combinations(data,2)]
    return float(sum(d)/len(d))


def perm(data, groups):
    n=len(data); levels=set(groups)
    ss_t=sum(bc(a,b)**2 for a,b in combinations(data,2))/n
    ss_w=Fraction(0)
    for g in levels:
        rows=[row for row,label in zip(data,groups) if label==g]
        ss_w += sum(bc(a,b)**2 for a,b in combinations(rows,2))/len(rows)
    ss_b=ss_t-ss_w
    return {"pseudo_f":float((ss_b/(len(levels)-1))/(ss_w/(n-len(levels)))),"r_squared":float(ss_b/ss_t)}


def rma(x,y):
    mx,my=math.fsum(x)/len(x),math.fsum(y)/len(y)
    xx=math.fsum((a-mx)**2 for a in x);yy=math.fsum((a-my)**2 for a in y)
    xy=math.fsum((a-mx)*(b-my) for a,b in zip(x,y))
    slope=math.copysign(math.sqrt(yy/xx),xy)
    return {"slope":slope,"intercept":my-slope*mx,"n":len(x)}


def shannon(row):
    return -math.fsum(float(v/sum(row))*math.log(float(v/sum(row))) for v in row if v)


def main():
    results={}
    item="P01-control";_,ids,data=table(item,transpose=True)
    rows=[r for sid,r in zip(ids,data) if sid!="5"]
    results[item]={"mean_bray_curtis":meanbc(rows),"n_cores":len(rows)}
    item="P02-control";_,_,data=table(item,transpose=True)
    results[item]=perm(data,[r["zone"] for r in meta(item,"field_log.csv")])
    item="P03-control";_,_,data=table(item,"assemblage.tsv")
    results[item]={"mean_bray_curtis":meanbc(relative(data))}
    item="P04-control";_,ids,data=table(item);campaign={r["core"]:r["campaign"] for r in meta(item,"cores.csv")}
    results[item]={}
    for group in ("2017","2021"):
        h=[shannon(r) for sid,r in zip(ids,data) if campaign[sid]==group]
        results[item][f"shannon_mean_{group}"]=math.fsum(h)/len(h)
    item="P05-control";names,_,data=table(item,"counts.txt")
    a,b=[names.index(n) for n in ("Globorotalia inflata","Globorotalia truncatulinoides")]
    rows=[[v for j,v in enumerate(row) if j not in (a,b)]+[row[a]+row[b]] for row in data]
    results[item]={"richness":len(names)-1,"mean_bray_curtis":meanbc(rows)}
    item="P06-control";_,_,data=table(item);groups=[r["zone"] for r in meta(item,"zones.csv")]
    rows=[[sum(r[j] for r in data[start:start+3]) for j in range(len(data[0]))] for start in range(0,len(data),3)]
    results[item]=perm(relative(rows),groups[::3])|{"n":len(rows)}
    item="P07-control";shells=meta(item,"shells.csv")
    def scaled(scale):
        x=[float(r["length"])*(scale if r["locality"]=="L3" else 1) for r in shells]
        y=[float(r["width"])*(scale if r["locality"]=="L3" else 1) for r in shells]
        return rma(x,y)|{"mean_length_mm":math.fsum(x)/len(x)}
    results[item]=scaled(.1); declared_cm_to_mm=scaled(10)
    item="P08-control";_,ids,data=table(item);epoch={r["sample"]:r["epoch"] for r in meta(item,"samples.csv")}
    rows=[r for sid,r in zip(ids,data) if epoch[sid]=="Holocene"]
    results[item]={"mean_bray_curtis":meanbc(rows),"n_samples":len(rows)}
    item="P09-control";rows=[r for r in meta(item,"valves.csv") if r["specimen"] not in {"V03","V11","V19","V25"}]
    results[item]=rma([float(r["length_mm"]) for r in rows],[float(r["height_mm"]) for r in rows])
    item="P10-control";_,ids,data=table(item);d=dict(zip(ids,data))
    results[item]={"shannon_change":shannon(d["S12"])-shannon(d["S1"])}
    item="P11-control";names,_,data=table(item,"species.txt")
    genus=["Globigerina" if n.split()[0]=="Globigerinoides" else n.split()[0] for n in names]
    levels=sorted(set(genus));rows=[[sum(v for v,g in zip(row,genus) if g==level) for level in levels] for row in data]
    results[item]={"mean_bray_curtis":meanbc(rows),"n_genera":len(levels)}
    item="P12-control";_,_,data=table(item)
    results[item]=perm(data,[r["zone"] for r in meta(item,"zones.csv")])|{"n":len(data)}
    frozen=json.loads((ROOT/"evaluation/pilot/flaws.json").read_text());checks={}
    for item,result in results.items():
        key=json.loads((ITEMS/item/"key.json").read_text());tol=key["tolerance"]
        errors={k:abs(v-frozen[item]["results"][k]) for k,v in result.items()}
        assert max(errors.values())<1e-12,(item,errors)
        separation={k:abs(v-key["results"][k])/max(tol["abs"],tol["rel"]*abs(key["results"][k])) for k,v in result.items()}
        if frozen[item]["class"]!="interpretation":assert max(separation.values())>1,(item,separation)
        checks[item]={"independent_results":result,"absolute_errors":errors,"separation_in_key_tolerances":separation}
    files=[Path(__file__),ROOT/"evaluation/pilot/flaws.py",ROOT/"evaluation/pilot/flaws.json",ROOT/"tests/test_pilot_flaws.py"]
    files += [p for item in results for p in sorted((ITEMS/item/"materials").iterdir())]
    receipt={"baseline":"aedc158","checks":checks,"p07_declared_cm_to_mm_results":declared_cm_to_mm,
             "p07_declared_vs_frozen_mean_length_delta":declared_cm_to_mm["mean_length_mm"]-results["P07-control"]["mean_length_mm"],
             "source_sha256":{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files},"inference_calls":0}
    (HERE/"receipt.json").write_text(json.dumps(receipt,indent=2)+"\n")
    print(json.dumps({"items":len(checks),"max_absolute_error":max(v for c in checks.values() for v in c["absolute_errors"].values()),"p07_declared_mean_length":declared_cm_to_mm["mean_length_mm"]}))


if __name__=="__main__":main()
