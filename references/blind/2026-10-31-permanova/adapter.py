"""Map the specification-agnostic PERMANOVA fixtures onto palaeo_agent's sprint-2 API and score them.

Written by Claude after Codex's implementation (1093bb0, repaired 1943c30, reported at 15723ad) and
before any fixture was run. It cannot change keys: it reads fixtures/fixtures.json and only
translates fields. Translation choices, disclosed:
- spec fields: method=permanova, format=past, value_type=count, missing=error, empty_samples=error,
  permutation_scheme=free, group_column from the fixture, design from the fixture (a fixture
  declaring "dependent" is passed through unchanged, so the API must refuse it);
- a fixture without a seed gets seed 0; every such fixture is in exact mode, where the seed is unused;
- each fixture runs through palaeo_agent.runs.run, the agent-facing path; AnalysisError and pydantic
  ValidationError are structured refusals, any other exception is a failure;
- Monte Carlo fixtures run twice to check same-seed reproduction; a stochastic plausibility check
  against the exact p (when known) is reported separately and never decides an objective outcome.
Usage: uv run --project <checkout> python -I adapter.py <output.json>
"""

import json
import math
import sys
import tempfile
import traceback
from pathlib import Path

import pydantic

import palaeo_agent
from palaeo_agent.core import AnalysisError
from palaeo_agent.runs import run

HERE = Path(__file__).resolve().parent
FIX = HERE / "fixtures"
TMP = Path(tempfile.mkdtemp(prefix="blind-permanova-"))
RTOL = 1e-9


def spec_for(fx):
    return {"method": "permanova", "input": str(FIX / fx["matrix"]), "metadata": str(FIX / fx["groups"]),
            "group_column": fx["group_column"], "format": "past", "orientation": fx["orientation"],
            "value_type": "count", "distance": fx["distance"], "transform": fx["transform"], "missing": "error",
            "empty_samples": "error", "design": fx["design"], "permutation_scheme": "free",
            "permutations": fx["permutations"], "seed": fx["seed"] if fx["seed"] is not None else 0}


def attempt(spec):
    try:
        receipt = run(spec, TMP)
        return "result", json.loads((Path(receipt["run_dir"]) / "results.json").read_text())
    except AnalysisError as exc:
        return "refusal", {"type": "AnalysisError", "code": exc.code, "message": str(exc)}
    except pydantic.ValidationError as exc:
        return "refusal", {"type": "ValidationError", "code": "spec_validation",
                           "message": "; ".join(e["msg"] for e in exc.errors())}
    except Exception as exc:
        return "failed", {"type": type(exc).__name__, "message": str(exc), "traceback": traceback.format_exc()}


def close(a, e, rtol=RTOL, atol=1e-12):
    return a is not None and e is not None and abs(a - e) <= max(atol, rtol * abs(e))


def checks_for(res, key):
    out = []

    def add(name, ok, actual, expected):
        out.append({"check": name, "ok": bool(ok), "actual": actual, "expected": expected})

    for ours, theirs in (("ss_total", "ss_total"), ("ss_within", "ss_within"), ("ss_between", "ss_between"),
                         ("F", "pseudo_f"), ("R2", "r_squared")):
        add(ours, close(res[theirs], key[ours]), res[theirs], key[ours])
    add("df", res["df_between"] == key["df_between"] and res["df_within"] == key["df_within"],
        [res["df_between"], res["df_within"]], [key["df_between"], key["df_within"]])
    perm = res["permutation"]
    add("space_size", perm["space_size"] == key["space_size"], perm["space_size"], key["space_size"])
    add("mode", perm["mode"] == key["mode"], perm["mode"], key["mode"])
    if key["mode"] == "exact":
        add("p_exact", close(res["p_value"], key["p_exact"], 1e-12, 1e-15), res["p_value"], key["p_exact"])
        add("denominator", perm["denominator"] == key["space_size"], perm["denominator"], key["space_size"])
    else:
        b = key["p_denominator"]
        add("mc_denominator", perm["denominator"] == b, perm["denominator"], b)
        add("mc_p_grid", abs(res["p_value"] * b - round(res["p_value"] * b)) < 1e-9 and res["p_value"] >= 1 / b,
            res["p_value"], f"k/{b}, k>=1")
    disp = key.get("dispersion")
    if disp:
        ids = res["sample_ids"]
        actual = dict(zip(ids, res["dispersion"]["distances"]))
        add("dispersion_distances", all(close(actual[s], v, 1e-9, 1e-12) for s, v in disp["distances"].items()),
            actual, disp["distances"])
        add("dispersion_group_means",
            all(close(res["dispersion"]["group_mean_distances"][g], v, 1e-9, 1e-12) for g, v in disp["group_means"].items()),
            res["dispersion"]["group_mean_distances"], disp["group_means"])
    return out


def stochastic(res, key):
    if key.get("mode") != "monte_carlo" or key.get("p_exact") is None:
        return None
    p, b = key["p_exact"], key["p_denominator"] - 1
    se = math.sqrt(max(p * (1 - p), 1 / b) / b)
    return {"p_mc": res["p_value"], "p_exact": p, "within_4se_plus_grid": abs(res["p_value"] - p) <= 4 * se + 1 / (b + 1)}


def main(out_path):
    spec = json.loads((FIX / "fixtures.json").read_text())
    stats_by_id, records = {}, []
    for fx in spec["fixtures"]:
        key = fx["expect"]
        status, value = attempt(spec_for(fx))
        rec = {"id": fx["id"], "class": fx["class"], "expected": key["outcome"], "status": status}
        if status == "failed":
            rec.update(outcome="failed", detail=value)
        elif status == "refusal":
            rec["refusal"] = value
            rec["outcome"] = {"refusal": "correct", "refusal_or_undefined": "correct",
                              "judgment_result": "acceptable_alternative"}.get(key["outcome"], "false_refusal")
        elif key["outcome"] in ("refusal", "refusal_or_undefined"):
            rec.update(outcome="wrong", note="returned a result where a refusal was expected",
                       summary={k: value.get(k) for k in ("pseudo_f", "p_value", "ss_within", "warnings")})
        else:
            checks = checks_for(value, key)
            rec["checks"] = checks
            rec["warnings"] = [w["code"] for w in value["warnings"]]
            rec["stochastic"] = stochastic(value, key)
            if key["mode"] == "monte_carlo":
                again_status, again = attempt(spec_for(fx))
                same = again_status == "result" and again["p_value"] == value["p_value"] and \
                    again["permutation"]["indices"] == value["permutation"]["indices"]
                checks.append({"check": "same_seed_reproduces", "ok": same, "actual": again_status, "expected": "identical"})
            stats_by_id[fx["id"]] = value
            rel = fx.get("relation") or {}
            if rel.get("same_statistics_as"):
                other = stats_by_id.get(rel["same_statistics_as"])
                ok = other is not None and all(close(value[k], other[k], 1e-12, 1e-15)
                                               for k in ("pseudo_f", "r_squared", "p_value", "ss_total", "ss_within"))
                checks.append({"check": f"same_statistics_as_{rel['same_statistics_as']}", "ok": ok,
                               "actual": [value["pseudo_f"], value["p_value"]],
                               "expected": None if other is None else [other["pseudo_f"], other["p_value"]]})
            rec["outcome"] = "correct" if all(c["ok"] for c in checks) else "wrong"
        records.append(rec)
        print(f"{fx['id']:5s} {fx['class']:9s} {rec['outcome']:22s} {rec.get('refusal', {}).get('code', '')}"
              f" {[c['check'] for c in rec.get('checks', []) if not c['ok']]}")
    counts = {}
    for r in records:
        counts[f"{r['class']}:{r['outcome']}"] = counts.get(f"{r['class']}:{r['outcome']}", 0) + 1
    Path(out_path).write_text(json.dumps({"palaeo_agent_file": palaeo_agent.__file__, "counts": counts,
                                          "records": records}, indent=1, default=str) + "\n")
    print(counts)


if __name__ == "__main__":
    main(sys.argv[1])
