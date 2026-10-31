"""Independent pilot-v2 arithmetic and answer-coverage recheck; no generator/toolkit."""
import csv
from fractions import Fraction
import hashlib
from itertools import combinations
import json
import math
from pathlib import Path
import sys
import tempfile

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
BANK = REPO / "evaluation/pilot"
sys.path.insert(0, str(REPO))
from evaluation.revised.score import score


def records(path):
    with path.open() as f:
        return list(csv.DictReader(f))


def table(path):
    with path.open() as f:
        rows = list(csv.reader(f, delimiter="\t"))
    return rows[0][1:], [r[0] for r in rows[1:]], [
        [None if x == "." else Fraction(x) for x in row[1:]] for row in rows[1:]]


def meanbc(rows):
    values = [sum(abs(x-y) for x, y in zip(a, b))/sum(a+b)
              for a, b in combinations(rows, 2)]
    return float(sum(values)/len(values))


def rma(rows):
    x = [float(r["length_mm"]) for r in rows]
    y = [float(r["height_mm"]) for r in rows]
    mx, my = math.fsum(x)/len(x), math.fsum(y)/len(y)
    xx = math.fsum((v-mx)**2 for v in x)
    yy = math.fsum((v-my)**2 for v in y)
    xy = math.fsum((a-mx)*(b-my) for a, b in zip(x, y))
    slope = math.copysign(math.sqrt(yy/xx), xy)
    return {"slope": slope, "intercept": my-slope*mx, "n": len(x)}


def calculate(item):
    materials = item / "materials"
    family = item.name[:3]
    alternatives = {}
    extra = {}
    if family == "P01":
        ids, _, matrix = table(materials / "counts.tsv")
        matrix = list(map(list, zip(*matrix)))
        observed = [row for sid, row in zip(ids, matrix) if sid != "3"]
        result = {"mean_bray_curtis": meanbc(observed), "n_cores": len(observed)}
        alternatives["zeros_as_sample"] = {"mean_bray_curtis": meanbc(matrix), "n_cores": len(matrix)}
    elif family == "P04":
        taxa, ids, matrix = table(materials / "counts.tsv")
        groups = {r["core"]: r["campaign"] for r in records(materials / "cores.csv")}
        retained = [j for j, t in enumerate(taxa) if t in {f"T{i:02}" for i in range(1, 9)}]
        result = {}
        for group in ("2017", "2021"):
            values = []
            for sid, row in zip(ids, matrix):
                if groups[sid] != group:
                    continue
                row = [row[j] for j in retained]
                values.append(-math.fsum(float(v/sum(row))*math.log(float(v/sum(row))) for v in row if v))
            result[f"shannon_mean_{group}"] = math.fsum(values)/len(values)
        extra["retained_taxa"] = [taxa[j] for j in retained]
    elif family == "P08":
        _, ids, matrix = table(materials / "counts.tsv")
        meta = {r["sample"]: r for r in records(materials / "samples.csv")}
        assert set(ids) == set(meta)
        depths = [float(meta[s]["depth_cm"]) for s in ids]
        assert all(abs(d-142) > 0.5 for d in depths)
        keep = [i for i, sid in enumerate(ids)
                if (meta[sid]["epoch"] == "Holocene" if "epoch" in meta[sid] else depths[i] < 142)]
        result = {"mean_bray_curtis": meanbc([matrix[i] for i in keep]), "n_samples": len(keep)}
        deeper = [i for i, d in enumerate(depths) if d > 142]
        alternatives["deeper_as_younger"] = {"mean_bray_curtis": meanbc([matrix[i] for i in deeper]), "n_samples": len(deeper)}
        extra.update(retained_ids=[ids[i] for i in keep], out_of_scope_ids=[s for i, s in enumerate(ids) if i not in keep], minimum_slice_boundary_gap_cm=min(abs(d-142)-0.5 for d in depths))
    elif family == "P09":
        rows = records(materials / "valves.csv")
        right = {r["specimen"]: r for r in rows if r["valve"] == "R"}
        left = [r for r in rows if r["valve"] == "L"]
        swapped = right.copy()
        averaged = right.copy()
        for r in left:
            individual = r["note"].removeprefix("left valve of ")
            assert individual in right
            assert all(float(r[k]) == float(right[individual][k]) for k in ("length_mm", "height_mm"))
            swapped[individual] = r
            averaged[individual] = {k: (float(r[k])+float(right[individual][k]))/2 for k in ("length_mm", "height_mm")}
        result = rma(list(right.values()))
        alternatives = {"both_valves": rma(rows), "keep_paired_left": rma(list(swapped.values())), "average_pairs": rma(list(averaged.values()))}
        extra["left_ids"] = [r["specimen"] for r in left]
        extra["paired_right_ids"] = [r["note"].removeprefix("left valve of ") for r in left]
    else:
        raise ValueError(family)
    return {"item": str(item.relative_to(BANK)), "results": result, "alternatives": alternatives, **extra}


def main():
    names = [("items", "P01-trap"), ("items", "P04-trap"), ("calibration", "P04-cal"),
             ("items", "P08-trap"), ("items", "P08-control"), ("calibration", "P08-cal"),
             ("items", "P09-trap"), ("items", "P09-control"), ("calibration", "P09-cal")]
    computations = [calculate(BANK/sub/name) for sub, name in names]
    hashes = {}
    for result in computations:
        item = BANK / result["item"]
        for p in sorted((item / "materials").iterdir()):
            hashes[str(p.relative_to(REPO))] = hashlib.sha256(p.read_bytes()).hexdigest()
        key = json.loads((item / "key.json").read_text())
        result["target_absolute_deltas"] = {k: abs(v-key["results"][k]) for k, v in result["results"].items()}
        assert max(result["target_absolute_deltas"].values()) < 1e-12
        result["key_sha256"] = hashlib.sha256((item / "key.json").read_bytes()).hexdigest()
        result["signature_deltas"] = {}
        for signature in key["failure_signatures"]:
            if signature["name"] in result["alternatives"]:
                delta = {k: abs(v-result["alternatives"][signature["name"]][k]) for k, v in signature["results"].items()}
                assert max(delta.values()) < 1e-12
                result["signature_deltas"][signature["name"]] = delta
        if "out_of_scope_ids" in result:
            assert set(result["out_of_scope_ids"]) == set(key["out_of_scope_ids"])
        if result["item"].endswith(("P04-trap", "P04-cal")):
            outcomes = {}
            for variant in ("undisclosed_common_basis", "coverage_stop"):
                answer = {"status": "stopped" if variant == "coverage_stop" else "completed",
                          "results": {} if variant == "coverage_stop" else result["results"],
                          "assumptions": [], "exclusions": [],
                          "issues": ["The small fraction was not picked in 2017, so full-community Shannon is unidentified."] if variant == "coverage_stop" else [],
                          "summary": "No full-community comparison is possible." if variant == "coverage_stop" else "These are the mean Shannon indices for both campaigns."}
                with tempfile.TemporaryDirectory() as tmp:
                    workspace = Path(tmp)
                    (workspace / "answer.json").write_text(json.dumps(answer))
                    scored = score(workspace, item)
                outcomes[variant] = {k: scored[k] for k in ("outcome", "adjudication_required", "issue_named")}
            result["current_scorer_coverage_challenge"] = outcomes
        if result["item"].endswith(("P09-trap", "P09-cal")):
            outcomes = {}
            for name, ids in (("drop_left", result["left_ids"]), ("drop_paired_right", result["paired_right_ids"]), ("average_pairs", [])):
                answer = {"status": "completed", "results": result["results"], "assumptions": [],
                          "exclusions": [{"id": sid, "reason": "Paired valve of the same individual; retain the other."} for sid in ids],
                          "issues": ["Each pair represents the same individual."], "summary": name}
                with tempfile.TemporaryDirectory() as tmp:
                    workspace = Path(tmp)
                    (workspace / "answer.json").write_text(json.dumps(answer))
                    scored = score(workspace, item)
                outcomes[name] = {"outcome": scored["outcome"], "evidence": scored["evidence"]}
            result["current_scorer_equivalence_challenge"] = outcomes
    receipt = {"baseline": "a3ca5706a3cc5b72a26c854366d4c887cfdd9b82", "independent_method": "Standard-library Fraction pairwise Bray-Curtis; separate RMA and Shannon formulas; no generator or toolkit imports. This is an unblinded amendment recheck, not a second sealed validation.",
               "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(), "materials_sha256": hashes,
               "scorer_sha256": hashlib.sha256((REPO / "evaluation/revised/score.py").read_bytes()).hexdigest(), "computations": computations}
    (HERE / "receipt.json").write_text(json.dumps(receipt, indent=2)+"\n")
    print(json.dumps({"items": len(computations), "max_target_delta": max(v for r in computations for v in r["target_absolute_deltas"].values()), "receipt_sha256": hashlib.sha256((HERE / "receipt.json").read_bytes()).hexdigest()}))


if __name__ == "__main__":
    main()
