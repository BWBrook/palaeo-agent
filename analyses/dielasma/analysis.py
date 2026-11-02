# /// script
# requires-python = ">=3.12"
# dependencies = ["numpy==2.5.4", "scipy==1.18.1"]
# ///
"""Dielasma allometry and locality differences: corrected derivative of authentic session A2.

Run from anywhere: `uv run analyses/dielasma/analysis.py`. Writes results.json beside this file.
Every inference is repeated under three L2 scenarios, because the archived L2 columns repeat a block.
"""

import hashlib
import json
from itertools import combinations
from pathlib import Path

import numpy as np
from scipy import stats
from scipy.optimize import minimize_scalar

HERE = Path(__file__).resolve().parent
DATA = HERE.parents[1] / "benchmarks/past/legacy-data/dielasma.dat"
SEED = 20261102
B_BOOT = 2000
B_PARAM = 1999
LOCS = ("L1", "L2", "L3")
PAIRS = list(combinations(LOCS, 2))

rows = [line.split() for line in DATA.read_text().splitlines() if line.strip()]
header = rows[0][1:]
raw = {}
for loc in LOCS:
    i, j = header.index(f"{loc}/X1"), header.index(f"{loc}/X2")
    raw[loc] = [(r[0], float(r[1 + i]), float(r[1 + j])) for r in rows[1:] if r[1 + i] != "."]


def repeats(records):
    """Exact repeated (X1, X2) pairs and maximal recurring runs of >= 3 consecutive specimens."""
    values = [(x, y) for _, x, y in records]
    ids = [r for r, _, _ in records]
    seen = {}
    for k, v in enumerate(values):
        seen.setdefault(v, []).append(ids[k])
    blocks = []
    for i in range(len(values)):
        for j in range(i + 1, len(values)):
            if values[i] != values[j] or (i and values[i - 1] == values[j - 1]):
                continue
            n = 0
            while j + n < len(values) and i + n < j and values[i + n] == values[j + n]:
                n += 1
            if n >= 3:
                blocks.append({"first": ids[i:i + n], "repeat": ids[j:j + n]})
    return {"repeated_pairs": {f"{x}/{y}": r for (x, y), r in seen.items() if len(r) > 1}, "blocks": blocks}


def unique_pairs(records):
    seen, out = set(), []
    for r in records:
        if (r[1], r[2]) not in seen:
            seen.add((r[1], r[2]))
            out.append(r)
    return out


scenarios = {
    "as_archived": raw,
    "block_removed": raw | {"L2": [r for r in raw["L2"] if not 64 <= int(r[0]) <= 70]},
    "unique_pairs": raw | {"L2": unique_pairs(raw["L2"])},
}


def sma(x, y, alpha=0.05):
    """Standardised major axis (= RMA) with the exact normal-theory interval and slope = 1 test (Warton et al. 2006)."""
    n = len(x)
    r = np.corrcoef(x, y)[0, 1]
    b = np.sign(r) * np.std(y, ddof=1) / np.std(x, ddof=1)
    t = stats.t.ppf(1 - alpha / 2, n - 2)
    q = (1 - r ** 2) * t ** 2 / (n - 2)
    ci = sorted([b * (np.sqrt(q + 1) - np.sqrt(q)), b * (np.sqrt(q + 1) + np.sqrt(q))])
    r_rf = np.corrcoef(y - x, y + x)[0, 1]
    t1 = r_rf * np.sqrt((n - 2) / (1 - r_rf ** 2))
    return {"n": n, "slope": float(b), "intercept": float(y.mean() - b * x.mean()), "r": float(r),
            "ci95": [float(c) for c in ci], "test_slope_1": {"r_resid_fitted": float(r_rf),
                                                             "p": float(2 * stats.t.sf(abs(t1), n - 2))}}


def ols(x, y):
    fit = stats.linregress(x, y)
    t = stats.t.ppf(0.975, len(x) - 2)
    return {"slope": float(fit.slope), "ci95": [float(fit.slope - t * fit.stderr), float(fit.slope + t * fit.stderr)],
            "p_slope_1": float(2 * stats.t.sf(abs((fit.slope - 1) / fit.stderr), len(x) - 2))}


def r_rf(x, y, b):
    return np.corrcoef(y - b * x, y + b * x)[0, 1]


def common_slope_stat(groups):
    """Warton & Weber (2002) likelihood ratio for a common SMA slope: minimise sum n_i log(1 - r_i(b)^2)."""
    lo = min(sma(x, y)["slope"] for x, y in groups) * 0.5
    hi = max(sma(x, y)["slope"] for x, y in groups) * 2
    f = lambda b: -sum(len(x) * np.log(1 - r_rf(x, y, b) ** 2) for x, y in groups)
    res = minimize_scalar(f, bounds=(lo, hi), method="bounded", options={"xatol": 1e-12})
    return float(res.fun), float(res.x)


def holm(p):
    order = np.argsort(p)
    adjusted, running = np.empty(len(p)), 0.0
    for rank, i in enumerate(order):
        running = max(running, min(1.0, (len(p) - rank) * p[i]))
        adjusted[i] = running
    return adjusted.tolist()


def em(v, mu, sd):
    n, w = len(v), np.array([0.5, 0.5])
    for _ in range(2000):
        dens = w * stats.norm.pdf(v[:, None], mu, sd)
        resp = dens / dens.sum(axis=1, keepdims=True)
        nk = resp.sum(axis=0)
        w, mu = nk / n, (resp * v[:, None]).sum(axis=0) / nk
        sd = np.maximum(np.sqrt((resp * (v[:, None] - mu) ** 2).sum(axis=0) / nk), 1e-6)
    return np.log((w * stats.norm.pdf(v[:, None], mu, sd)).sum(axis=1)).sum(), w, mu, sd


def mixture_bic(v):
    """BIC for one versus two Gaussians on log length; EM from a grid of starts, best likelihood kept."""
    n = len(v)
    one = -2 * stats.norm.logpdf(v, v.mean(), v.std()).sum() + 2 * np.log(n)
    starts = [(np.quantile(v, [a, b]), np.full(2, f * v.std())) for a in (0.05, 0.15, 0.25, 0.4)
              for b in (0.6, 0.75, 0.85, 0.95) for f in (1.0, 0.5, 0.25)]
    ll, w, mu, sd = max((em(v, m, s) for m, s in starts), key=lambda fit: fit[0])
    order = np.argsort(mu)
    grid = np.linspace(np.exp(v.min()), np.exp(v.max()), 20001)
    density = sum(wk * stats.lognorm.pdf(grid, sk, scale=np.exp(mk)) for wk, mk, sk in zip(w, mu, sd))
    peaks = grid[1:-1][(density[1:-1] > density[:-2]) & (density[1:-1] > density[2:])]
    return {"bic_one": float(one), "bic_two": float(-2 * ll + 5 * np.log(n)), "starts": len(starts),
            "component_medians": [float(np.exp(mu[k])) for k in order],
            "component_weights": [float(w[k]) for k in order],
            "fitted_density_modes": [float(x) for x in peaks]}


def analyse(data, rng):
    out = {"n": {k: len(v) for k, v in data.items()}}
    L = {k: np.log10([r[1] for r in v]) for k, v in data.items()}
    W = {k: np.log10([r[2] for r in v]) for k, v in data.items()}
    length = {k: np.array([r[1] for r in v]) for k, v in data.items()}
    ratio = {k: np.array([r[2] / r[1] for r in v]) for k, v in data.items()}

    out["sma_log10_width_on_length"] = {}
    for k in LOCS:
        fit = sma(L[k], W[k])
        idx = np.arange(len(L[k]))
        boot = []
        for _ in range(B_BOOT):
            s = rng.choice(idx, len(idx))
            boot.append(sma(L[k][s], W[k][s])["slope"])
        fit["bootstrap_ci95"] = [float(np.quantile(boot, 0.025)), float(np.quantile(boot, 0.975))]
        fit["ols"] = ols(L[k], W[k])
        fit["quadratic_term_p"] = float(_quadratic_p(L[k], W[k]))
        out["sma_log10_width_on_length"][k] = fit

    groups = [(L[k], W[k]) for k in LOCS]
    stat, b_common = common_slope_stat(groups)
    sims = []
    for _ in range(B_PARAM):
        sim = []
        for x, y in groups:
            rr = np.corrcoef(x, y)[0, 1]
            sx = np.std(x, ddof=1)
            cov = [[sx ** 2, rr * sx * b_common * sx], [rr * sx * b_common * sx, (b_common * sx) ** 2]]
            z = rng.multivariate_normal([0, 0], cov, len(x))
            sim.append((z[:, 0], z[:, 1]))
        sims.append(common_slope_stat(sim)[0])
    # Nonparametric null: centre each group, rescale width to the common SMA slope, resample observed pairs.
    nulls = []
    for x, y in groups:
        xc, yc = x - x.mean(), y - y.mean()
        nulls.append((xc, yc * b_common * np.std(xc, ddof=1) / np.std(yc, ddof=1)))
    resampled = []
    for _ in range(B_PARAM):
        resampled.append(common_slope_stat([(x[s], y[s]) for x, y in nulls for s in [rng.choice(len(x), len(x))]])[0])
    out["common_slope"] = {"slope": b_common, "lr": stat, "p_chi2": float(stats.chi2.sf(stat, len(LOCS) - 1)),
                           "p_parametric_bootstrap": float((np.sum(np.array(sims) >= stat) + 1) / (B_PARAM + 1)),
                           "p_pairs_bootstrap": float((np.sum(np.array(resampled) >= stat) + 1) / (B_PARAM + 1))}
    boot = []
    for _ in range(B_BOOT):
        resampled = [(x[s], y[s]) for x, y in groups for s in [rng.choice(len(x), len(x))]]
        boot.append(common_slope_stat(resampled)[1])
    out["common_slope"]["bootstrap_ci95"] = [float(np.quantile(boot, 0.025)), float(np.quantile(boot, 0.975))]
    pair_p = [stats.chi2.sf(common_slope_stat([(L[a], W[a]), (L[b], W[b])])[0], 1) for a, b in PAIRS]
    out["common_slope_pairwise"] = {f"{a}-{b}": {"p_chi2": float(p), "p_bonferroni": float(min(1, 3 * p))}
                                    for (a, b), p in zip(PAIRS, pair_p)}

    elev = {k: W[k] - b_common * L[k] for k in LOCS}
    out["elevation_at_common_slope"] = {k: float(v.mean()) for k, v in elev.items()}
    tests = [stats.ttest_ind(elev[a], elev[b], equal_var=False).pvalue for a, b in PAIRS]
    out["elevation_pairwise_welch"] = {f"{a}-{b}": {"p": float(p), "p_bonferroni": float(min(1, 3 * p))}
                                       for (a, b), p in zip(PAIRS, tests)}
    out["elevation_welch_anova_p"] = _welch_anova_p([elev[k] for k in LOCS])

    out["length"] = {k: {"mean": float(v.mean()), "median": float(np.median(v)), "min": float(v.min()),
                         "max": float(v.max())} for k, v in length.items()}
    out["length_kruskal_p"] = float(stats.kruskal(*length.values()).pvalue)
    out["shapiro_log_length_p"] = {k: float(stats.shapiro(np.log(v)).pvalue) for k, v in length.items()}
    out["length_pairwise"] = {}
    for a, b in PAIRS:
        mw = stats.mannwhitneyu(length[a], length[b], alternative="two-sided").pvalue
        ks = stats.ks_2samp(length[a], length[b]).pvalue
        out["length_pairwise"][f"{a}-{b}"] = {"mann_whitney_p": float(mw), "mann_whitney_p_bonferroni": float(min(1, 3 * mw)),
                                              "ks_p": float(ks), "ks_p_bonferroni": float(min(1, 3 * ks))}
    out["length_histogram_bins"] = np.arange(2, 28, 2).tolist()
    out["length_histogram"] = {k: np.histogram(v, bins=np.arange(2, 28, 2))[0].tolist() for k, v in length.items()}
    out["log_length_mixture"] = {k: mixture_bic(np.log(v)) for k, v in length.items()}

    out["width_length_ratio"] = {k: {"mean": float(v.mean()), "sd": float(v.std(ddof=1))} for k, v in ratio.items()}
    out["ratio_kruskal_p"] = float(stats.kruskal(*ratio.values()).pvalue)
    out["ratio_pairwise_mann_whitney"] = {}
    for a, b in PAIRS:
        p = stats.mannwhitneyu(ratio[a], ratio[b], alternative="two-sided").pvalue
        out["ratio_pairwise_mann_whitney"][f"{a}-{b}"] = {"p": float(p), "p_bonferroni": float(min(1, 3 * p))}
    out["residual_sd_log10"] = {k: float(np.std(W[k] - (out["sma_log10_width_on_length"][k]["intercept"] +
                                                       out["sma_log10_width_on_length"][k]["slope"] * L[k]), ddof=2))
                                for k in LOCS}
    return out


def _quadratic_p(x, y):
    X = np.column_stack([np.ones_like(x), x - x.mean(), (x - x.mean()) ** 2])
    beta, rss, *_ = np.linalg.lstsq(X, y, rcond=None)
    resid = y - X @ beta
    s2 = resid @ resid / (len(x) - 3)
    se = np.sqrt(s2 * np.linalg.inv(X.T @ X)[2, 2])
    return 2 * stats.t.sf(abs(beta[2] / se), len(x) - 3)


def _welch_anova_p(samples):
    n = np.array([len(s) for s in samples])
    m = np.array([s.mean() for s in samples])
    v = np.array([s.var(ddof=1) for s in samples])
    w = n / v
    mw = (w * m).sum() / w.sum()
    k = len(samples)
    a = (w * (m - mw) ** 2).sum() / (k - 1)
    lam = ((1 - w / w.sum()) ** 2 / (n - 1)).sum()
    f = a / (1 + 2 * (k - 2) * lam / (k ** 2 - 1))
    return float(stats.f.sf(f, k - 1, (k ** 2 - 1) / (3 * lam)))


results = {"source": {"file": "benchmarks/past/legacy-data/dielasma.dat", "sha256": hashlib.sha256(DATA.read_bytes()).hexdigest()},
           "seed": SEED, "data_integrity": {k: repeats(v) for k, v in raw.items()},
           "scenarios": {name: {"L2_rows_removed": sorted(set(r[0] for r in raw["L2"]) - set(r[0] for r in data["L2"]),
                                                          key=int),
                                **analyse(data, np.random.default_rng(SEED))}
                         for name, data in scenarios.items()}}
(HERE / "results.json").write_text(json.dumps(results, indent=1) + "\n")
