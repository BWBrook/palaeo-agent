"""Run blind fixtures through Palaeo-Agent's agent-facing run path.

Usage: uv run --project <checkout> python -I runner.py <fixtures_dir> <output.json>
Each community/RMA fixture goes through palaeo_agent.runs.run (spec parsing,
calculation, result validation, bundle writing); sensitivity fixtures through
run + compare_community_runs. AnalysisError or pydantic ValidationError is a
structured refusal; any other exception is a failure.
"""

import hashlib
import json
import sys
import tempfile
import traceback
from pathlib import Path

import numpy as np
import pydantic

import palaeo_agent
from palaeo_agent.core import AnalysisError
from palaeo_agent.runs import run
from palaeo_agent.sensitivity import compare_community_runs

FIX = Path(sys.argv[1]).resolve()
OUT = Path(sys.argv[2]).resolve()
TMP = Path(tempfile.mkdtemp(prefix="blind-runs-"))


def resolve(spec):
    spec = dict(spec)
    for key in ("input", "metadata"):
        if key in spec:
            spec[key] = str(FIX / spec[key])
    return spec


def attempt(fn):
    try:
        return "result", fn()
    except AnalysisError as exc:
        return "refusal", {"type": "AnalysisError", "code": exc.code, "message": str(exc),
                           "details": json.loads(json.dumps(getattr(exc, "details", {}), default=str))}
    except pydantic.ValidationError as exc:
        return "refusal", {"type": "ValidationError", "code": "spec_validation",
                           "message": "; ".join(e["msg"] for e in exc.errors())}
    except Exception as exc:
        return "failed", {"type": type(exc).__name__, "message": str(exc), "traceback": traceback.format_exc()}


def run_one(spec):
    receipt = run(resolve(spec), TMP)
    return json.loads((Path(receipt["run_dir"]) / "results.json").read_text()), receipt["run_dir"]


def derived(result, path):
    if path in ("slope", "intercept", "correlation", "n", "n_input", "sample_ids", "positive_gram",
                "pearson_distance_correlation", "spearman_distance_correlation", "symmetric_procrustes_m2",
                "raw_count_total_imbalance_bound"):
        return result[path]
    if path == "residuals":
        return [pair["residual"] for pair in result["pairs"]]
    if path in ("warning_codes", "warning_codes_include"):
        return sorted(w["code"] for w in result["warnings"])
    if path == "excluded_ids":
        return sorted(e["sample_id"] for e in result["excluded"])
    if path == "excluded_reasons":
        return sorted({e["reason"] for e in result["excluded"]})
    if path == "distance_pairs":
        ids = result["sample_ids"]
        return {f"{a}|{b}": result["distances"][i][j] for i, a in enumerate(ids) for j, b in enumerate(ids) if i < j}
    if path == "diversity_by_id":
        return {d["sample_id"]: d for d in result["diversity"]}
    lam = np.asarray(result.get("eigenvalues", []), float)
    if path == "eigenvalues_nonnull_desc":
        return sorted((float(v) for v in lam if abs(v) > 1e-8 * np.abs(lam).max()), reverse=True)
    if path == "eigen_trace":
        return float(lam.sum())
    if path == "eigen_sumsq":
        return float((lam ** 2).sum())
    if path == "negative_count":
        return len(result["negative_eigenvalues"])
    if path == "abs_axis1":
        return [abs(row[0]) for row in result["coordinates"]]
    raise KeyError(path)


def close(actual, expected, tol):
    if isinstance(expected, dict):
        if not isinstance(actual, dict) or set(expected) - set(actual):
            return False
        return all(close(actual[k], v, tol) for k, v in expected.items())
    if isinstance(expected, list):
        return isinstance(actual, list) and len(actual) == len(expected) and all(
            close(a, e, tol) for a, e in zip(actual, expected))
    if isinstance(expected, str) or tol == 0:
        return actual == expected
    return abs(actual - expected) <= tol * max(1.0, abs(expected))


def evaluate_checks(result, checks):
    out = []
    for path, expected, tol in checks:
        actual = derived(result, path)
        if path == "warning_codes_include":
            ok = expected in actual
        elif path == "diversity_by_id":
            ok = all(actual.get(s, {}).get("richness") == e["richness"] and actual[s]["total"] == e["total"]
                     and close(actual[s]["shannon"], e["shannon"], tol) and close(actual[s]["simpson"], e["simpson"], tol)
                     for s, e in expected.items())
        else:
            ok = close(actual, expected, tol)
        out.append({"path": path, "ok": ok, "expected": expected, "actual": actual, "tol": tol})
    return out


def relation(kind, a, b, params, rtol):
    if kind == "rma_swap":
        pairs = [("slope_product", a["slope"] * b["slope"], 1.0),
                 ("intercept_swapped", b["intercept"], -a["intercept"] / a["slope"]),
                 ("r_equal", b["correlation"], a["correlation"])]
    elif kind == "rma_affine":
        sx, cx, sy, cy = params["sx"], params["cx"], params["sy"], params["cy"]
        slope = sy * a["slope"] / sx
        pairs = [("slope", b["slope"], slope), ("intercept", b["intercept"], sy * a["intercept"] - slope * cx + cy),
                 ("r", b["correlation"], a["correlation"] * (1 if sx * sy > 0 else -1))]
    return [{"path": name, "ok": close(actual, expected, rtol), "expected": expected, "actual": actual, "tol": rtol}
            for name, actual, expected in pairs]


def manifest_hash(run_dir):
    return hashlib.sha256((Path(run_dir) / "manifest.json").read_bytes()).hexdigest()


def execute(fx):
    exp = fx["expect"]
    want = exp["outcome"]
    if fx["family"] == "sensitivity":
        status, value = attempt(lambda: run_one(fx["spec"]["baseline"]))
        if status != "result":
            return {"outcome": "failed", "stage": "baseline", "detail": value}
        base_result, base_dir = value
        second = dict(fx["spec"]["sensitivity"])
        second.setdefault("baseline_run", manifest_hash(base_dir))

        def compare():
            _, sens_dir = run_one(second)
            receipt = compare_community_runs(base_dir, sens_dir, TMP)
            return json.loads((Path(receipt["comparison_dir"]) / "report.json").read_text())
        status, value = attempt(compare)
    elif want == "relation":
        status, value = attempt(lambda: (run_one(fx["spec"])[0], run_one(exp["partner"])[0]))
    else:
        status, value = attempt(lambda: run_one(fx["spec"])[0])

    record = {"status": status}
    if status == "failed":
        return dict(record, outcome="failed", detail=value)
    if status == "refusal":
        record["refusal"] = value
        return dict(record, outcome="correct" if want in ("refusal", "refusal_or_warning") else "false_refusal")
    if want == "refusal":
        return dict(record, outcome="wrong", note="Returned a result where a refusal was expected",
                    summary={k: value.get(k) for k in ("n", "slope", "correlation", "eigenvalues", "warnings") if k in value})
    if want == "refusal_or_warning":
        codes = [w["code"] for w in value.get("warnings", [])]
        return dict(record, outcome="correct" if exp["warning"] in codes else "wrong", warning_codes=codes)
    if want == "relation":
        checks = relation(exp["relation"], value[0], value[1], exp.get("params"), exp["rtol"])
    else:
        checks = evaluate_checks(value, exp["checks"])
    record["checks"] = checks
    return dict(record, outcome="correct" if all(c["ok"] for c in checks) else "wrong")


spec = json.loads((FIX / "fixtures.json").read_text())
results = []
for fx in spec["fixtures"]:
    r = execute(fx)
    results.append({"id": fx["id"], "family": fx["family"], "class": fx["class"], "purpose": fx["purpose"],
                    "expected": fx["expect"]["outcome"], **r})
    print(f"{fx['id']:5s} {r['outcome']:14s} {r.get('refusal', {}).get('code', '')}")

counts = {}
for r in results:
    counts[r["outcome"]] = counts.get(r["outcome"], 0) + 1
OUT.write_text(json.dumps({"palaeo_agent_file": palaeo_agent.__file__, "counts": counts, "results": results},
                          indent=1, default=str) + "\n")
print(counts)
