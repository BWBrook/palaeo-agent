"""Prototype of the revision-2 exact numerical model (Claude, 12 Nov 2026). Artificial data only; not the implementation."""
import math
import numpy as np
from fractions import Fraction
TINY = 2.0**-1022

def rounded_sqrt(q):  # nearest double to sqrt(q), q a positive Fraction; ties to even
    y = math.sqrt(float(q))
    while True:
        lo, hi = math.nextafter(y, 0), math.nextafter(y, math.inf)
        # midpoints
        mlo, mhi = (Fraction(y) + Fraction(lo)) / 2, (Fraction(y) + Fraction(hi)) / 2
        if mlo * mlo > q: y = lo; continue
        if mhi * mhi < q: y = hi; continue
        if mlo * mlo == q and (math.frexp(y)[0] * 2**53) % 2: y = lo; continue  # tie: prefer even
        if mhi * mhi == q and (math.frexp(y)[0] * 2**53) % 2: y = hi; continue
        return y

def coordinates(rows, transform):
    out = []
    for row in rows:
        total = sum(Fraction(v) for v in row)
        if total == 0: raise ValueError("empty")
        c = []
        for v in row:
            q = Fraction(v) / total
            x = 0.0 if q == 0 else (float(q) if transform == "relative_abundance" else rounded_sqrt(q))
            if q > 0 and x < TINY: raise ValueError("numerical_range: coordinate")
            c.append(x)
        out.append(c)
    return out

def hierarchy(X):
    # integer representation on common dyadic scale
    E = min((math.frexp(v)[1] - 53 for row in X for v in row if v), default=0)
    ints = [[int(Fraction(v) / Fraction(2) ** E) for v in row] for row in X]   # exact
    n, p = len(X), len(X[0])
    S = [list(r) for r in ints]; size = [1] * n; first = list(range(n)); last = list(range(n))
    scale = Fraction(2) ** (2 * E)
    def cost(a, b):
        na, nb = size[a], size[b]
        num = sum((nb * x - na * y) ** 2 for x, y in zip(S[a], S[b]))
        return Fraction(num, na * nb * (na + nb))
    clusters = list(range(n)); costs = [cost(i, i + 1) for i in range(n - 1)]
    merges = []; H = Fraction(0)
    while len(clusters) > 1:
        j = min(range(len(costs)), key=lambda k: (costs[k], k))
        others = costs[:j] + costs[j + 1:]
        runner = min(others) if others else None
        a, b = clusters[j], clusters[j + 1]
        c = costs[j] * scale; H += c
        merges.append({"boundary": last[a], "cost": c, "runner_up": None if runner is None else runner * scale, "cumulative": H})
        S[a] = [x + y for x, y in zip(S[a], S[b])]; size[a] += size[b]; last[a] = last[b]
        del clusters[j + 1]; del costs[j]
        if j > 0: costs[j - 1] = cost(clusters[j - 1], a)
        if j < len(clusters) - 1: costs[j] = cost(a, clusters[j + 1])
    m = len(merges); Hm = H
    bs = []
    for r in range(1, m + 1):
        g = merges[m - r]["cost"]; e = Hm / m * sum(Fraction(1, k) for k in range(r, m + 1))
        bs.append((r, g, e, g > e))
    k = 1
    for r, g, e, ok in bs:
        if not ok: break
        k += 1
    reported = [x["cost"] for x in merges] + [x["cumulative"] for x in merges] + [e for *_, e, _ in bs]
    if any(0 < v < TINY for v in reported): raise ValueError("numerical_range: reported quantity")
    return merges, bs, k

def direct_ss(rows):
    v = [[Fraction(x) for x in r] for r in rows]; n = len(v)
    mean = [sum(c) / n for c in zip(*v)]
    return sum((x - mu) ** 2 for r in v for x, mu in zip(r, mean))

def lw(X):  # rioja recurrence on squared euclid
    X=np.asarray(X,float); n=len(X); D=((X[:,None]-X[None])**2).sum(-1)
    idx=list(range(n)); size=[1]*n; e=0; ret={}
    while len(idx)>1:
        ds=[D[idx[k],idx[k+1]] for k in range(len(idx)-1)]
        p=0
        for k in range(1,len(ds)):
            if ds[k]<ds[p]: p=k
        a,b=idx[p],idx[p+1]; e+=0.5*ds[p]
        # boundary label = first original sample of right cluster minus 1
        ret[b]=e
        for o in idx:
            if o in (a,b): continue
            nr=size[o]; D[a,o]=D[o,a]=((nr+size[a])*D[o,a]+(nr+size[b])*D[o,b]-nr*ds[p])/(nr+size[a]+size[b])
        size[a]+=size[b]; idx.remove(b)
    return ret

def main():

    for t in ("relative_abundance", "hellinger"):
        m, bs, k = hierarchy(coordinates([[1, 9]] * 4, t))
        assert all(x["cost"] == 0 for x in m) and k == 1
        X = coordinates([[1, 1], [1, 1 + 1e-15], [1, 1 + 2e-15]], t)
        m, bs, k = hierarchy(X)
        assert m[-1]["cumulative"] == direct_ss(X)
    try:
        hierarchy(coordinates([[1, 1e-200], [1, 2e-200], [1, 3e-200]], "relative_abundance"))
        raise AssertionError("underflow not refused")
    except ValueError as exc:
        assert "numerical_range" in str(exc)
    rng = np.random.default_rng(5)
    for _ in range(100):
        counts = rng.integers(0, 50, (15, 6)); counts[:, 0] += 1
        X = coordinates(counts.tolist(), "hellinger"); m, bs, k = hierarchy(X)
        r = lw(np.array(X))
        assert all(abs(float(x["cumulative"]) - r[x["boundary"] + 1]) <= 1e-12 * float(m[-1]["cumulative"]) for x in m)
        bounds = set(range(14))
        for x in m:
            bounds.discard(x["boundary"]); cuts = [-1] + sorted(bounds) + [14]
            assert sum(direct_ss(X[cuts[i] + 1:cuts[i + 1] + 1]) for i in range(len(cuts) - 1)) == x["cumulative"]
    print("all checks passed")


if __name__ == "__main__":
    main()
