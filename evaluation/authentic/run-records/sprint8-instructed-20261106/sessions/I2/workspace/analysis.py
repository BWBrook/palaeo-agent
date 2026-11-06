"""Dielasma allometry and locality comparison. Run: python analysis.py"""
import json, os, shutil, itertools
import numpy as np, pandas as pd
from scipy import stats
import palaeo_agent

SEED = 20240611
rng = np.random.default_rng(SEED)
LOCS = ["L1", "L2", "L3"]
os.makedirs("specs", exist_ok=True)
BUNDLES = "bundles"
shutil.rmtree(BUNDLES, ignore_errors=True)
os.makedirs(BUNDLES)

res = {}
pr = palaeo_agent.primer()
prov = {"primer_version": pr["version"], "primer_sha256": pr["sha256"], "runs": {}}

# --- supported: RMA per locality (log10, plus raw-scale sensitivity), via toolkit
for tr in ["log10", "none"]:
    for L in LOCS:
        spec = dict(method="rma", input="dielasma.dat", format="past", x=f"{L}/X1",
                    y=f"{L}/X2", transform=tr, missing="drop_pairs")
        name = f"rma_{L}_{tr}"
        json.dump(spec, open(f"specs/{name}.json", "w"), indent=1)
        v = palaeo_agent.validate(spec)
        out = palaeo_agent.run(spec, BUNDLES)
        prov["runs"][name] = str(out)
        run_dir = out if isinstance(out, (str, os.PathLike)) else (out.get("run_dir") or out.get("path"))
        r = palaeo_agent.inspect_run(run_dir)["result"]
        res[name] = {k: r[k] for k in ["n_input", "n", "mean_x", "mean_y", "sd_x", "sd_y",
                                       "correlation", "slope", "intercept", "vertical_residual_rmse"]}
        res[name]["warnings"] = [{"code": w["code"], "details": w.get("details")} for w in r["warnings"]]
        res[name]["validate_warnings"] = [w["code"] for w in v.get("warnings", [])]

# --- unsupported by toolkit (declared in report): parsing for bootstrap, CIs, group tests
rows = [l.split() for l in open("dielasma.dat").read().strip().splitlines()]
hdr = rows[0][1:]
df = pd.DataFrame([[np.nan if c == "." else float(c) for c in r[1:]] for r in rows[1:]], columns=hdr)
D = {L: df[[f"{L}/X1", f"{L}/X2"]].dropna().to_numpy() for L in LOCS}
LD = {L: np.log10(D[L]) for L in LOCS}


def rma(a):
    x, y = a[:, 0], a[:, 1]
    s = np.sign(np.corrcoef(x, y)[0, 1]) * y.std(ddof=1) / x.std(ddof=1)
    return s, y.mean() - s * x.mean()


B = 10000
boot = {}
for L in LOCS:
    a = LD[L]; n = len(a)
    sl = np.array([rma(a[rng.integers(0, n, n)])[0] for _ in range(B)])
    boot[L] = sl
    lo, hi = np.percentile(sl, [2.5, 97.5])
    res[f"rma_{L}_log10"].update(
        slope_boot_ci95=[lo, hi], isometry_slope1_in_ci=bool(lo <= 1 <= hi),
        toolkit_slope_matches_own=bool(abs(rma(a)[0] - res[f"rma_{L}_log10"]["slope"]) < 1e-9),
        ols_slope=float(stats.linregress(a[:, 0], a[:, 1]).slope))
for p, q in itertools.combinations(LOCS, 2):
    res[f"slope_diff_{p}_{q}"] = dict(diff=float(rma(LD[p])[0] - rma(LD[q])[0]),
                                      ci95=list(np.percentile(boot[p] - boot[q], [2.5, 97.5])))

ratio = {L: D[L][:, 1] / D[L][:, 0] for L in LOCS}
length = {L: D[L][:, 0] for L in LOCS}
summ = {}
for L in LOCS:
    x, y = D[L][:, 0], D[L][:, 1]
    h, _ = np.histogram(x, bins=np.arange(0, 28, 2))
    summ[L] = dict(n=len(x), length_mean=x.mean(), length_median=float(np.median(x)),
                   length_sd=x.std(ddof=1), length_min=x.min(), length_max=x.max(),
                   length_skew=float(stats.skew(x)), width_mean=y.mean(),
                   ratio_mean=float(ratio[L].mean()), ratio_sd=float(ratio[L].std(ddof=1)),
                   frac_length_lt_10=float(np.mean(x < 10)),
                   length_hist_2unit_bins_0_26=h.tolist())
res["summary"] = summ
k = stats.kruskal(*length.values()); res["kruskal_length"] = dict(H=k.statistic, p=k.pvalue)
k = stats.kruskal(*ratio.values()); res["kruskal_ratio"] = dict(H=k.statistic, p=k.pvalue)
pl = []
for p, q in itertools.combinations(LOCS, 2):
    for nm, src in [("length", length), ("ratio", ratio)]:
        m = stats.mannwhitneyu(src[p], src[q]); ks = stats.ks_2samp(src[p], src[q])
        pl.append(dict(var=nm, pair=f"{p}-{q}", mwu_U=m.statistic, mwu_p=m.pvalue,
                       ks_D=ks.statistic, ks_p=ks.pvalue))
ps = np.array([t["mwu_p"] for t in pl]); order = np.argsort(ps); run = 0.0
for rank, i in enumerate(order):
    run = max(run, min(1.0, (len(ps) - rank) * ps[i])); pl[i]["mwu_p_holm6"] = run
res["pairwise"] = pl

# repeated-pair check on L2 and sensitivity with repeats removed
l2 = D["L2"].tolist(); seen = set(); ndup = 0
for r in l2:
    ndup += tuple(r) in seen; seen.add(tuple(r))
res["L2_exact_duplicate_pairs"] = dict(n_dup=ndup, n_unique=len(seen))
u = np.unique(np.log10(D["L2"]), axis=0); n = len(u)
sl = np.array([rma(u[rng.integers(0, n, n)])[0] for _ in range(B)])
res["L2_unique_only_log10"] = dict(n=n, slope=rma(u)[0], slope_boot_ci95=list(np.percentile(sl, [2.5, 97.5])))

json.dump(res, open("results.json", "w"), indent=1, default=float)
json.dump(prov, open("provenance_manifest.json", "w"), indent=1)
