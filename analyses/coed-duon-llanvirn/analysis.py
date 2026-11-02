# /// script
# requires-python = ">=3.12"
# dependencies = ["numpy==2.5.4", "scipy==1.18.1"]
# ///
"""Coed Duon (Upper Llanvirn) assemblage change: corrected derivative of authentic session A1.

Run from anywhere: `uv run analyses/coed-duon-llanvirn/analysis.py`. Writes results.json beside this file.
"""

import json
from pathlib import Path

import numpy as np
from scipy.stats import fisher_exact, spearmanr

HERE = Path(__file__).resolve().parent
DATA = HERE.parents[1] / "benchmarks/past/legacy-data/llanvirn.dat"
SEED = 20261102
B_NULL = 4999
B_BOOT = 2000
R_RARE = 2000
FOCAL = [(5, 6), (6, 7)]

rows = [line.split() for line in DATA.read_text().splitlines() if line.strip()]
horizons = [int(h) for h in rows[0][1:]]
labels = [r[0] for r in rows[1:]]
taxa = [label[3:] if label[0] == "_" and label[2] == "_" else label for label in labels]
X = np.array([[int(v) for v in r[1:]] for r in rows[1:]])
col = {h: X[:, i] for i, h in enumerate(horizons)}
N = {h: int(col[h].sum()) for h in horizons}
rng = np.random.default_rng(SEED)
steps = [(a, a + 1) for a in horizons[:-1]]
key = lambda a, b: f"{a}-{b}"


def bc(u, v):
    return float(np.abs(u - v).sum() / (u + v).sum())


def holm(p):
    order = np.argsort(p)
    adjusted, running = np.empty(len(p)), 0.0
    for rank, i in enumerate(order):
        running = max(running, min(1.0, (len(p) - rank) * p[i]))
        adjusted[i] = running
    return adjusted.tolist()


def rarefy(c, n):
    return rng.multivariate_hypergeometric(c, n)


out = {"source": {"file": "benchmarks/past/legacy-data/llanvirn.dat",
                  "sha256": __import__("hashlib").sha256(DATA.read_bytes()).hexdigest()},
       "seed": SEED, "taxa": taxa, "label_codes": {t: l[:3] for t, l in zip(taxa, labels)},
       "totals": N, "richness": {h: int((col[h] > 0).sum()) for h in horizons}}
P = {h: col[h] / N[h] for h in horizons}
i_sow, i_bas = taxa.index("Sower"), taxa.index("Basil")
out["proportion"] = {t: {h: round(float(P[h][i]), 6) for h in horizons} for i, t in enumerate(taxa)}
out["spearman_total_richness"] = dict(zip(("rho", "p"), map(float, spearmanr(list(N.values()),
                                                                             list(out["richness"].values())))))

# Diversity, with rarefaction to the smallest total; intervals are within-sample (hypergeometric) only.
n_min = min(N.values())
out["rarefaction_n"] = n_min
out["shannon"] = {h: float(-(p[p > 0] * np.log(p[p > 0])).sum()) for h, p in P.items()}
out["inverse_simpson"] = {h: float(1 / (p ** 2).sum()) for h, p in P.items()}
rare = {h: np.array([(rarefy(col[h], n_min) > 0).sum() for _ in range(R_RARE)]) for h in horizons}
out["rarefied_richness"] = {h: {"mean": float(r.mean()), "q025": float(np.quantile(r, 0.025)),
                                "q975": float(np.quantile(r, 0.975))} for h, r in rare.items()}

# Adjacent dissimilarity under total-independent representations, plus the confounded raw log for contrast.
std = lambda h, n: P[h] * n
reps = {"proportion": lambda h: P[h], "sqrt_proportion": lambda h: np.sqrt(P[h]),
        "log1p_per_100": lambda h: np.log1p(std(h, 100)), "log1p_per_13": lambda h: np.log1p(std(h, n_min)),
        "log1p_raw_counts_confounded": lambda h: np.log1p(col[h])}
out["bray_curtis"] = {name: {key(a, b): bc(f(a), f(b)) for a, b in steps} for name, f in reps.items()}
presence = {}
for a, b in steps:
    draws = [bc((rarefy(col[a], n_min) > 0) * 1.0, (rarefy(col[b], n_min) > 0) * 1.0) for _ in range(R_RARE)]
    presence[key(a, b)] = {"mean": float(np.mean(draws)), "q025": float(np.quantile(draws, 0.025)),
                           "q975": float(np.quantile(draws, 0.975))}
out["sorensen_rarefied"] = presence
out["sorensen_observed_confounded"] = {key(a, b): bc((col[a] > 0) * 1.0, (col[b] > 0) * 1.0) for a, b in steps}
out["rank_of_focal_steps"] = {name: {key(a, b): int(sorted(v.values(), reverse=True).index(v[key(a, b)]) + 1)
                                     for a, b in FOCAL} for name, v in out["bray_curtis"].items()}

# Overall-composition homogeneity at fixed totals: one test per adjacent step, Holm across the nine.
null = {}
for a, b in steps:
    pooled = (col[a] + col[b]) / (N[a] + N[b])
    obs = bc(P[a], P[b])
    sims = np.array([bc(rng.multinomial(N[a], pooled) / N[a], rng.multinomial(N[b], pooled) / N[b])
                     for _ in range(B_NULL)])
    null[key(a, b)] = {"observed": obs, "null_median": float(np.median(sims)), "null_q95": float(np.quantile(sims, 0.95)),
                       "p": float((np.sum(sims >= obs) + 1) / (B_NULL + 1))}
for (k, v), adj in zip(null.items(), holm([v["p"] for v in null.values()])):
    v["p_holm"] = adj
out["composition_null"] = null

# Counting-error bootstrap of proportional BC; it cannot place mass on unobserved taxa.
out["bray_curtis_bootstrap"] = {}
for a, b in steps:
    sims = [bc(rng.multinomial(N[a], P[a]) / N[a], rng.multinomial(N[b], P[b]) / N[b]) for _ in range(B_BOOT)]
    out["bray_curtis_bootstrap"][key(a, b)] = [float(np.quantile(sims, q)) for q in (0.025, 0.5, 0.975)]

# Focal transitions: per-taxon Fisher tests with Holm over the taxa present at either horizon, observed
# gains and losses, and how likely the observed absence would be if the other horizon's proportion held.
for a, b in FOCAL:
    present = [i for i in range(len(taxa)) if col[a][i] + col[b][i] > 0]
    tests = [fisher_exact([[col[a][i], N[a] - col[a][i]], [col[b][i], N[b] - col[b][i]]])[1] for i in present]
    adjusted = holm(tests)
    out[f"taxa_{a}_{b}"] = {taxa[i]: {"count_a": int(col[a][i]), "count_b": int(col[b][i]),
                                      "prop_a": float(P[a][i]), "prop_b": float(P[b][i]),
                                      "fisher_p": float(p), "p_holm": float(q)}
                            for i, p, q in zip(present, tests, adjusted)}
    gained = [i for i in present if col[a][i] == 0]
    lost = [i for i in present if col[b][i] == 0]
    out[f"membership_{a}_{b}"] = {
        "shared": int(sum(1 for i in present if col[a][i] and col[b][i])),
        "gained": {taxa[i]: {"count_b": int(col[b][i]), "p_zero_at_a_given_prop_b": float((1 - P[b][i]) ** N[a])}
                   for i in gained},
        "lost": {taxa[i]: {"count_a": int(col[a][i]), "p_zero_at_b_given_prop_a": float((1 - P[a][i]) ** N[b])}
                 for i in lost},
        "upper95_proportion_of_taxon_unseen_at_b": float(1 - 0.05 ** (1 / N[b]))}
    rest = [i for i in range(len(taxa)) if i != i_sow]
    rest2 = [i for i in rest if i != i_bas]
    out[f"without_dominants_{a}_{b}"] = {
        "n_a_excl_Sower": int(col[a][rest].sum()), "n_b_excl_Sower": int(col[b][rest].sum()),
        "bc_excl_Sower": bc(col[a][rest] / col[a][rest].sum(), col[b][rest] / col[b][rest].sum()),
        "n_a_excl_Sower_Basil": int(col[a][rest2].sum()), "n_b_excl_Sower_Basil": int(col[b][rest2].sum()),
        "bc_excl_Sower_Basil": bc(col[a][rest2] / col[a][rest2].sum(), col[b][rest2] / col[b][rest2].sum())}

# Lithostratigraphic units: pooled taxon composition (specimen-weighted) and PCoA of sqrt-proportion BC.
units = {"upper_flags_and_grits_1_6": [1, 2, 3, 4, 5, 6], "ashes_and_lavas_7_10": [7, 8, 9, 10]}
out["pooled_composition"] = {}
for unit, hs in units.items():
    c = sum(col[h] for h in hs)
    out["pooled_composition"][unit] = {"n": int(c.sum()), **{t: round(float(v), 6) for t, v in zip(taxa, c / c.sum())}}
D = np.array([[bc(np.sqrt(P[i]), np.sqrt(P[j])) for j in horizons] for i in horizons])
J = np.eye(len(horizons)) - 1 / len(horizons)
w, v = np.linalg.eigh(-0.5 * J @ D ** 2 @ J)
order = np.argsort(w)[::-1]
axis1 = v[:, order[0]] * np.sqrt(w[order[0]])
axis1 *= np.sign(axis1[horizons.index(10)] - axis1[horizons.index(1)])
out["pcoa_sqrt_proportion"] = {"axis1_share_of_positive_eigenvalues": float(w[order[0]] / w[w > 0].sum()),
                               "negative_eigenvalue_share": float(-w[w < 0].sum() / w[w > 0].sum()),
                               "axis1": {h: float(s) for h, s in zip(horizons, axis1)}}

(HERE / "results.json").write_text(json.dumps(out, indent=1) + "\n")
