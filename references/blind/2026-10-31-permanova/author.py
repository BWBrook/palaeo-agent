"""Author specification-agnostic blind fixtures for sprint-2 one-way PERMANOVA.

Claude (Opus 5.5), 31 October 2026, before Codex starts sprint 2. Does not import palaeo_agent.
PERMANOVA keys follow Anderson (2001) in exact rational arithmetic on exactly computed
Bray-Curtis or binary Jaccard distances:
  SS_T = (1/N) sum_{i<j} d_ij^2,  SS_W = sum_g (1/n_g) sum_{i<j in g} d_ij^2,  SS_A = SS_T - SS_W,
  F = (SS_A/(a-1)) / (SS_W/(N-a)),  R2 = SS_A/SS_T.
Exact p enumerates every distinct labelled allocation preserving group sizes, the observed
allocation once, and counts F >= F_obs over M allocations. An undefined permuted F (SS_W = 0
with SS_A > 0) is +inf and counts as at least as extreme. Dispersion keys come from vegan
(author_vegan.R) and are merged by merge_vegan.py.
"""

import itertools
import json
import math
import shutil
from fractions import Fraction as F
from pathlib import Path

import numpy as np

OUT = Path(__file__).resolve().parent / "fixtures"
FIXTURES = []
DEFAULT_B = 999


def bc(a, b):
    return F(sum(abs(x - y) for x, y in zip(a, b)), sum(a) + sum(b))


def jaccard(a, b):
    sa, sb = {i for i, x in enumerate(a) if x}, {i for i, x in enumerate(b) if x}
    return F(len(sa ^ sb), len(sa | sb))


def distances(counts, distance, transform):
    rows = counts
    if transform == "relative_abundance":
        rows = [[F(x, sum(r)) for x in r] for r in counts]
    fn = bc if distance == "braycurtis" else jaccard
    n = len(rows)
    return [[fn(rows[i], rows[j]) if i != j else F(0) for j in range(n)] for i in range(n)]


def stats(d, labels):
    n = len(labels)
    groups = sorted(set(labels))
    a = len(groups)
    sst = sum(d[i][j] ** 2 for i in range(n) for j in range(i + 1, n)) / n
    ssw = F(0)
    for g in groups:
        idx = [i for i in range(n) if labels[i] == g]
        ssw += sum(d[i][j] ** 2 for x, i in enumerate(idx) for j in idx[x + 1:]) / len(idx)
    ssa = sst - ssw
    if ssw == 0:
        fstat = math.inf if ssa > 0 else None
    else:
        fstat = (ssa / (a - 1)) / (ssw / (n - a))
    return {"ss_total": sst, "ss_within": ssw, "ss_between": ssa, "df_between": a - 1, "df_within": n - a,
            "F": fstat, "R2": ssa / sst if sst else None}


def allocations(labels):
    """Distinct labelled allocations preserving group sizes."""
    groups = sorted(set(labels))
    sizes = [labels.count(g) for g in groups]
    n = len(labels)

    def rec(remaining, k):
        if k == len(groups) - 1:
            yield [(groups[k], tuple(remaining))]
            return
        for combo in itertools.combinations(remaining, sizes[k]):
            rest = [i for i in remaining if i not in combo]
            for tail in rec(rest, k + 1):
                yield [(groups[k], combo)] + tail

    for alloc in rec(list(range(n)), 0):
        out = [None] * n
        for g, members in alloc:
            for i in members:
                out[i] = g
        yield out


def space_size(labels):
    n = len(labels)
    m = math.factorial(n)
    for g in set(labels):
        m //= math.factorial(labels.count(g))
    return m


def exact_p(d, labels):
    observed = stats(d, labels)["F"]
    count = total = 0
    for alloc in allocations(labels):
        f = stats(d, alloc)["F"]
        total += 1
        if f is None:
            raise ValueError("undefined permuted statistic with zero total variation")
        if f >= observed:
            count += 1
    assert total == space_size(labels)
    return F(count, total), total


def num(x):
    if isinstance(x, F):
        return float(x)
    return x


def write_matrix(name, samples, taxa, counts):
    lines = ["\t".join(["."] + taxa)] + ["\t".join([s] + [str(c) for c in row]) for s, row in zip(samples, counts)]
    (OUT / name).write_text("\n".join(lines) + "\n")


def write_groups(name, rows):
    (OUT / name).write_text("sample_id,group\n" + "".join(f"{s},{g}\n" for s, g in rows))


def fixture(fid, purpose, counts, labels, *, distance="braycurtis", transform="none", permutations=DEFAULT_B,
            seed=None, design="independent", expect="result", cls="objective", taxa=None, samples=None,
            group_rows=None, relation=None, note=None):
    samples = samples or [f"s{i + 1:02d}" for i in range(len(counts))]
    taxa = taxa or [f"t{j + 1}" for j in range(len(counts[0]))]
    write_matrix(f"{fid}.tsv", samples, taxa, counts)
    write_groups(f"{fid}-groups.csv", group_rows or list(zip(samples, labels)))
    spec = {"id": fid, "class": cls, "purpose": purpose, "matrix": f"{fid}.tsv", "orientation": "samples_by_taxa",
            "value_type": "count", "groups": f"{fid}-groups.csv", "group_column": "group", "distance": distance,
            "transform": transform, "permutations": permutations, "seed": seed, "design": design}
    key = {"outcome": expect}
    if expect in ("result", "judgment_result"):
        d = distances(counts, distance, transform)
        s = stats(d, labels)
        m = space_size(labels)
        mode = "exact" if (m - 1 <= permutations and m <= 10_000) else "monte_carlo"
        key.update({k: num(v) for k, v in s.items()}, space_size=m, mode=mode, sample_ids=samples)
        key["exact_rational"] = {k: f"{v.numerator}/{v.denominator}" for k, v in s.items() if isinstance(v, F)}
        if mode == "exact" or m <= 2000:
            p, total = exact_p(d, labels)
            key["p_exact"] = float(p)
            key["p_exact_rational"] = f"{p.numerator}/{p.denominator}"
        if mode == "monte_carlo":
            key["p_denominator"] = permutations + 1
        key["distance_matrix_rational"] = [[f"{x.numerator}/{x.denominator}" for x in row] for row in d]
    if note:
        key["note"] = note
    FIXTURES.append({**spec, "expect": key, "relation": relation})


# ---------- generators ----------

def grouped(seed, sizes, n_taxa, shift=1.0, conc=1.5, total=(60, 160)):
    g = np.random.default_rng(seed)
    centres = [g.dirichlet(np.full(n_taxa, conc)) for _ in sizes]
    counts, labels = [], []
    for k, (size, centre) in enumerate(zip(sizes, centres)):
        for _ in range(size):
            p = (1 - shift) * np.full(n_taxa, 1 / n_taxa) + shift * g.dirichlet(centre * 25 + 0.2)
            counts.append([int(x) for x in g.multinomial(int(g.integers(*total)), p / p.sum())])
            labels.append(f"g{k + 1}")
    return counts, labels


def main():
    shutil.rmtree(OUT, ignore_errors=True)
    OUT.mkdir()

    c, l = grouped(1, [3, 3], 6)
    fixture("P01", "Two groups of three, raw Bray-Curtis; exact enumeration of 20 allocations", c, l)
    fixture("P11", "P01 with sample rows reordered; statistics and exact p unchanged", [c[i] for i in (4, 0, 5, 2, 1, 3)],
            [l[i] for i in (4, 0, 5, 2, 1, 3)], samples=[f"s{i + 1:02d}" for i in (4, 0, 5, 2, 1, 3)],
            relation={"same_statistics_as": "P01"})

    c2, l2 = grouped(2, [2, 3, 4], 7)
    fixture("P02", "Three unequal groups (2/3/4), B=9999 requested so all 1260 allocations are enumerated", c2, l2,
            permutations=9999)
    fixture("P02b", "P02 at the default B=999: 1260 allocations exceed B+1, so Monte Carlo; F and R2 exact", c2, l2,
            seed=11)
    fixture("P13", "P02 with group labels renamed and listed in another order; statistics unchanged", c2,
            [{"g1": "zeta", "g2": "alpha", "g3": "mid"}[x] for x in l2], permutations=9999,
            relation={"same_statistics_as": "P02"})

    c3, l3 = grouped(3, [4, 4], 6, total=(30, 900))
    fixture("P03", "Relative-abundance Bray-Curtis with very unequal totals", c3, l3, transform="relative_abundance")
    fixture("P12", "P03 counts multiplied by 1000: relative-abundance statistics unchanged", [[x * 1000 for x in r] for r in c3],
            l3, transform="relative_abundance", relation={"same_statistics_as": "P03"})
    fixture("P04", "Binary Jaccard on the P03 counts", c3, l3, distance="jaccard")

    disjoint = [[5 if j == i else 0 for j in range(6)] for i in range(6)]
    fixture("P05", "Disjoint supports: every distance is 1, every allocation ties, F=1, R2=0.2, exact p=1", disjoint,
            ["a", "a", "a", "b", "b", "b"])

    tight = [[40, 1, 0, 0], [38, 2, 1, 0], [41, 0, 1, 1], [39, 1, 2, 0],
             [0, 1, 40, 2], [1, 0, 39, 3], [0, 2, 41, 1], [1, 1, 38, 2]]
    fixture("P06", "Two well-separated groups of four: observed and label-swapped allocations share the maximum F; p=2/70",
            tight, ["x"] * 4 + ["y"] * 4)

    c7, l7 = grouped(7, [6, 6], 8, shift=0.6)
    fixture("P07", "6/6 groups: M=924 <= B+1 at default B=999, so exact", c7, l7)
    c8, l8 = grouped(8, [7, 6], 8, shift=0.6)
    fixture("P08", "7/6 groups: M=1716 exceeds default B+1, so Monte Carlo; F, R2 exact", c8, l8, seed=8)
    fixture("P09", "P08 with B=9999 requested: M-1 <= B and M <= 10000, so all 1716 allocations are enumerated", c8, l8,
            permutations=9999)
    c10, l10 = grouped(10, [10, 10], 9, shift=0.5)
    fixture("P10", "10/10 groups: M=184756, Monte Carlo; the same seed must reproduce the same p", c10, l10, seed=20261031)

    ident = [[10, 5, 0, 1]] * 3 + [[0, 2, 9, 4]] * 3
    fixture("P14", "Zero within-group variation with between-group variation: F is undefined (infinite), not a finite number",
            ident, ["u"] * 3 + ["v"] * 3, expect="refusal_or_undefined")
    trio = [[10, 0, 2], [0, 10, 3], [4, 4, 9], [10, 0, 2], [0, 10, 3], [4, 4, 9]]
    fixture("P15", "Observed F finite, but the allocation grouping identical profiles has SS_W=0 (F=+inf); key counts it as more extreme",
            trio, ["p", "q", "r", "q", "r", "p"], cls="judgment", expect="judgment_result",
            note="Preferred treatment: an undefined permuted F with SS_A>0 is +inf and counts as extreme. A structured refusal citing undefined permutation statistics is an acceptable alternative; silently dropping or redrawing it is wrong.")

    base, bl = grouped(16, [3, 3], 5)
    fixture("P16", "Only one group: refuse", base, ["only"] * 6, expect="refusal")
    fixture("P17", "A group with one sample: refuse", base[:4], ["a", "a", "a", "b"], expect="refusal")
    samples = [f"s{i + 1:02d}" for i in range(6)]
    fixture("P18", "A sample with an empty group label: refuse", base, bl,
            group_rows=list(zip(samples, ["g1", "g1", "", "g2", "g2", "g2"])), expect="refusal")
    fixture("P19", "Group file names a sample absent from the matrix and omits one present: refuse (ID mismatch)", base, bl,
            group_rows=list(zip(samples[:5] + ["s99"], bl)), expect="refusal")
    fixture("P20", "Dependent sampling units declared (blocked subsamples): unsupported design, refuse", base, bl,
            design="dependent", expect="refusal")
    empty = [r[:] for r in base]
    empty[2] = [0] * 5
    fixture("P21", "An empty sample under Bray-Curtis: refuse rather than invent distances", empty, bl, expect="refusal")
    fixture("P22", "Numeric-looking group labels (1, 2) are categories", base, ["1", "1", "1", "2", "2", "2"])

    noneuc = [[0, 5, 6, 0, 0], [7, 5, 0, 1, 0], [5, 0, 0, 0, 5], [0, 1, 0, 0, 5], [0, 0, 5, 0, 3],
              [6, 4, 1, 0, 0], [0, 0, 4, 1, 4]]
    fixture("P23", "Non-Euclidean Bray-Curtis configuration (negative PCoA eigenvalues) for the dispersion diagnostic",
            noneuc, ["a", "a", "a", "b", "b", "b", "b"])
    g = np.random.default_rng(24)
    centre = np.array([0.3, 0.25, 0.2, 0.15, 0.1])
    spread = []
    for k, scale in enumerate([200.0] * 5 + [6.0] * 5):
        spread.append([int(x) for x in g.multinomial(150, g.dirichlet(centre * scale))])
    fixture("P24", "Similar centroids, different spreads: the dispersion diagnostic must show the difference", spread,
            ["tight"] * 5 + ["loose"] * 5)

    (OUT / "fixtures.json").write_text(json.dumps({"default_permutations": DEFAULT_B, "fixtures": FIXTURES}, indent=1) + "\n")
    print(len(FIXTURES), "fixtures")


if __name__ == "__main__":
    main()
