"""Author blind validation fixtures for Palaeo-Agent (Claude, Opus 5.5, 31 Oct 2026).

Keys come from the method definitions, computed here with exact rational
arithmetic where possible (fractions.Fraction) and numpy eigh only for
eigenvalues of exactly computed double-centred matrices. Nothing here imports
palaeo_agent. Outputs go to fixtures/: data files plus fixtures.json.
"""

import json
import math
from decimal import Decimal
from fractions import Fraction as F
from pathlib import Path

import numpy as np

OUT = Path(__file__).resolve().parent / "fixtures"
DATA = OUT / "data"
DATA.mkdir(parents=True, exist_ok=True)
fixtures = []


def write(name, text, *, raw=None):
    path = DATA / name
    if raw is not None:
        path.write_bytes(raw)
    else:
        path.write_text(text, encoding="utf-8", newline="\n")
    return f"data/{name}"


def past_columns(header, rows):
    lines = [". " + " ".join(header)]
    lines += [" ".join([rid, *[str(v) for v in vals]]) for rid, vals in rows]
    return "\n".join(lines) + "\n"


def add(fid, family, cls, purpose, spec, expect):
    fixtures.append({"id": fid, "family": family, "class": cls, "purpose": purpose,
                     "spec": spec, "expect": expect})


def rma_spec(path, x="X", y="Y", transform="none", missing="error"):
    return {"method": "rma", "input": path, "format": "past", "x": x, "y": y,
            "transform": transform, "missing": missing}


def rma_key(xs, ys):
    n = len(xs)
    mx, my = sum(xs) / n, sum(ys) / n
    sxx = sum((x - mx) ** 2 for x in xs)
    syy = sum((y - my) ** 2 for y in ys)
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    r = sxy / math.sqrt(sxx * syy)
    slope = math.copysign(math.sqrt(syy / sxx), sxy)
    return slope, my - slope * mx, r


def two_col(name, xs, ys, ids=None):
    ids = ids or [str(i + 1) for i in range(len(xs))]
    return write(name, past_columns(["X", "Y"], list(zip(ids, [(a, b) for a, b in zip(xs, ys)]))))


# ---------------------------------------------------------------- RMA
xs, ys = [1, 2, 3, 4, 5], [3, 5, 7, 9, 11]
p = two_col("r01.dat", xs, ys)
add("R01", "rma", "analytic", "Exact line y = 2x + 1", rma_spec(p),
    {"outcome": "result", "checks": [["slope", 2.0, 1e-12], ["intercept", 1.0, 1e-12], ["correlation", 1.0, 1e-12],
                                     ["n", 5, 0], ["residuals", [0.0] * 5, 1e-12], ["warning_codes", [], 0]]})

xs, ys = [-2, -1, 0, 1, 2], [4, 3, -1, -1, -5]
p = two_col("r02.dat", xs, ys)
a, r = -math.sqrt(5.2), -22 / math.sqrt(520)
add("R02", "rma", "analytic", "Negative association: slope -sqrt(Syy/Sxx), intercept 0, r = -22/sqrt(520)",
    rma_spec(p), {"outcome": "result", "checks": [["slope", a, 1e-12], ["intercept", 0.0, 1e-12],
                  ["correlation", r, 1e-12], ["residuals", [y - a * x for x, y in zip(xs, ys)], 1e-12]]})

xs = ["2.1", "3.7", "4.4", "5.9", "7.2", "8.8"]
ys = ["1.3", "2.9", "2.6", "4.8", "5.1", "6.9"]
p = two_col("r03.dat", xs, ys)
add("R03", "rma", "metamorphic", "RMA symmetry: swapping x and y inverts the slope; intercept becomes -b/a; r unchanged",
    rma_spec(p), {"outcome": "relation", "relation": "rma_swap", "partner": rma_spec(p, x="Y", y="X"), "rtol": 1e-12})

x2 = [str(Decimal("0.5") * Decimal(v) - 3) for v in xs]
y2 = [str(Decimal(10) * Decimal(v) + 7) for v in ys]
p = write("r04.dat", past_columns(["X", "Y", "X2", "Y2"],
                                  [(str(i + 1), row) for i, row in enumerate(zip(xs, ys, x2, y2))]))
add("R04", "rma", "metamorphic", "Affine equivariance: x' = 0.5x - 3, y' = 10y + 7 gives slope' = 20a, intercept' = 60a + 10b + 7, r' = r",
    rma_spec(p), {"outcome": "relation", "relation": "rma_affine", "partner": rma_spec(p, x="X2", y="Y2"),
                  "params": {"sx": 0.5, "cx": -3, "sy": 10, "cy": 7}, "rtol": 1e-12})

xs = [1, 2, 4, 8, 16, 32]
ys = [repr(3 * x ** 0.75) for x in xs]
p = two_col("r05.dat", xs, ys)
add("R05", "rma", "analytic", "log10 of exact power law y = 3 x^0.75: slope 0.75, intercept log10(3), r = 1",
    rma_spec(p, transform="log10"), {"outcome": "result", "checks": [["slope", 0.75, 1e-12],
                  ["intercept", math.log10(3), 1e-12], ["correlation", 1.0, 1e-12]]})

p = two_col("r06.dat", [0, 1, 2, 4, 8], [1, 2, 3, 5, 9])
add("R06a", "rma", "adversarial", "Zero x under log10 with missing='error' must be refused, not dropped",
    rma_spec(p, transform="log10"), {"outcome": "refusal"})
add("R06b", "rma", "adversarial", "Zero x under log10 with missing='drop_pairs': a zero is not a declared missing value; refuse",
    rma_spec(p, transform="log10", missing="drop_pairs"), {"outcome": "refusal"})

p = two_col("r07.dat", [5, 5, 5, 5], [1, 2, 3, 4])
add("R07", "rma", "adversarial", "Zero variance in x: RMA undefined", rma_spec(p), {"outcome": "refusal"})
p = two_col("r08.dat", [1, 2, 3, 4], [5, 5, 5, 5])
add("R08", "rma", "adversarial", "Zero variance in y: r undefined, slope sign undetermined", rma_spec(p), {"outcome": "refusal"})
p = two_col("r09.dat", [-1, 1, -1, 1], [-1, -1, 1, 1])
add("R09", "rma", "adversarial", "r exactly 0: the sign of the RMA slope is undefined", rma_spec(p), {"outcome": "refusal"})

xs = [-3, -2, -1, 0, 1, 2, 3, 4]
ys = [0.5, -1, 1, 0, -0.5, 1, -1, 0.4]
sl, ic, rr = rma_key(xs, ys)
p = two_col("r09b.dat", xs, ys)
add("R09b", "rma", "judgment", f"Near-zero correlation (r = {rr:.4g}): fit is defined but must carry a near-zero-correlation diagnostic",
    rma_spec(p), {"outcome": "result", "checks": [["slope", sl, 1e-12], ["intercept", ic, 1e-12], ["correlation", rr, 1e-12],
                  ["warning_codes_include", "near_zero_correlation", 0]]})

xs = [100000000 + k for k in range(5)]
p = two_col("r10.dat", xs, [2 * x + 1 for x in xs])
add("R10", "rma", "adversarial", "Large offset (1e8): naive sum-of-squares formulas lose all precision",
    rma_spec(p), {"outcome": "result", "checks": [["slope", 2.0, 1e-9], ["intercept", 1.0, 1e-6], ["correlation", 1.0, 1e-12]]})

xs = [f"{k}e-12" for k in range(1, 6)]
p = two_col("r11.dat", xs, [f"{3 * k}e-12" for k in range(1, 6)])
add("R11", "rma", "adversarial", "Tiny scale (1e-12): no absolute thresholds that misfire on small magnitudes",
    rma_spec(p), {"outcome": "result", "checks": [["slope", 3.0, 1e-12], ["intercept", 0.0, 1e-22], ["correlation", 1.0, 1e-12]]})

rows = [(str(i + 1), (x, y)) for i, (x, y) in enumerate(zip([1, 2, 3, 4, 5, ".", 7], [3, 5, 7, 9, 11, 13, "."]))]
p = write("r12.dat", past_columns(["X", "Y"], rows))
add("R12", "rma", "adversarial", "Declared missing '.' with missing='error' must be refused", rma_spec(p), {"outcome": "refusal"})
add("R13", "rma", "analytic", "missing='drop_pairs' excludes exactly the incomplete pairs, by ID, and fits the rest",
    rma_spec(p, missing="drop_pairs"), {"outcome": "result", "checks": [["slope", 2.0, 1e-12], ["intercept", 1.0, 1e-12],
                  ["n", 5, 0], ["n_input", 7, 0], ["excluded_ids", ["6", "7"], 0]]})

p = two_col("r14.dat", [1, 2, 3, 4], [2, 4, 5, 9], ids=["1", "2", "2", "3"])
add("R14", "rma", "adversarial", "Duplicate sample IDs must be refused", rma_spec(p), {"outcome": "refusal"})
p = write("r15.dat", past_columns(["X", "Y"], [("1", (1, 3)), ("2", (2, "NA")), ("3", (3, 7)), ("4", (4, 9))]))
add("R15", "rma", "adversarial", "'NA' is not the declared missing marker; refuse rather than treat as missing",
    rma_spec(p, missing="drop_pairs"), {"outcome": "refusal"})

text = past_columns(["X", "Y"], [(str(i + 1), (x, y)) for i, (x, y) in enumerate(zip([1, 2, 3, 4, 5], [3, 5, 7, 9, 11]))])
p = write("r16.dat", None, raw=b"\xef\xbb\xbf" + text.replace("\n", "\r\n").encode())
add("R16", "rma", "adversarial", "UTF-8 BOM and CRLF line endings parse identically to R01", rma_spec(p),
    {"outcome": "result", "checks": [["slope", 2.0, 1e-12], ["intercept", 1.0, 1e-12], ["n", 5, 0]]})
p = write("r17.dat", ".\tX\tY  \n" + "".join(f"{i + 1}\t{x}\t{y}\t \n" for i, (x, y) in enumerate(zip([1, 2, 3, 4, 5], [3, 5, 7, 9, 11]))))
add("R17", "rma", "adversarial", "Tab separators and trailing whitespace parse identically to R01", rma_spec(p),
    {"outcome": "result", "checks": [["slope", 2.0, 1e-12], ["intercept", 1.0, 1e-12], ["n", 5, 0]]})

p = two_col("r18.dat", [1, 4], [2, 8])
add("R18", "rma", "analytic", "Two pairs: slope = dy/dx = 2, r = 1, with a two-pairs diagnostic", rma_spec(p),
    {"outcome": "result", "checks": [["slope", 2.0, 1e-12], ["intercept", 0.0, 1e-12], ["correlation", 1.0, 1e-12],
                                     ["warning_codes_include", "two_pairs", 0]]})
p = two_col("r19.dat", [1, 2, "1e400", 4], [2, 4, 6, 8])
add("R19", "rma", "adversarial", "Overflowing token 1e400 (parses to inf) must be refused", rma_spec(p), {"outcome": "refusal"})
p = two_col("r20.dat", [1, 2, 3], [2, 4, 7])
add("R20", "rma", "adversarial", "x and y name the same column", rma_spec(p, x="X", y="X"), {"outcome": "refusal"})
add("R21", "rma", "adversarial", "Unknown column label (case differs)", rma_spec(p, x="x"), {"outcome": "refusal"})
p = write("r22.dat", ". X Y\n1 1 2\n2 2\n3 3 7\n")
add("R22", "rma", "adversarial", "Ragged row", rma_spec(p), {"outcome": "refusal"})
p = write("r23.dat", None, raw=". X Y\n1 1 2\n2 2 4\n3 3 7\n\xc9 4 8\n".encode("latin-1"))
add("R23", "rma", "adversarial", "Latin-1 bytes (not UTF-8) must be refused, not mis-decoded", rma_spec(p), {"outcome": "refusal"})
p = write("r24.dat", "id X Y\n1 1 2\n2 2 4\n3 3 7\n")
add("R24", "rma", "adversarial", "Header not in classic PAST form", rma_spec(p), {"outcome": "refusal"})
p = write("r25.dat", "")
add("R25", "rma", "adversarial", "Empty file", rma_spec(p), {"outcome": "refusal"})

# ---------------------------------------------------------------- community
SAMPLES = {"s1": [5, 5, 5, 5], "s2": [10, 0, 0, 0], "s3": [1, 1, 0, 0], "s4": [1, 2, 3, 4]}
TAXA = ["t1", "t2", "t3", "t4"]


def taxa_file(name, samples, taxa=TAXA):
    ids = list(samples)
    rows = [(t, [samples[s][i] for s in ids]) for i, t in enumerate(taxa)]
    return write(name, past_columns(ids, rows))


def comm_spec(path, transform="none", distance="braycurtis", dims=2, orientation="taxa_by_samples",
              empty="error", metadata=None):
    spec = {"method": "community", "input": path, "format": "past", "orientation": orientation,
            "value_type": "count", "transform": transform, "distance": distance, "dimensions": dims,
            "missing": "error", "empty_samples": empty}
    if metadata:
        spec["metadata"] = metadata
    return spec


def bc(x, y):
    return F(sum(abs(a - b) for a, b in zip(x, y)), sum(a + b for a, b in zip(x, y)))


def rel(x):
    total = sum(x)
    return [F(a, total) for a in x]


def jac(x, y):
    A = {i for i, a in enumerate(x) if a > 0}
    B = {i for i, b in enumerate(y) if b > 0}
    return 1 - F(len(A & B), len(A | B))


def dist_fn(transform, distance):
    if distance == "jaccard":
        return jac
    if transform == "relative_abundance":
        return lambda x, y: bc(rel(x), rel(y))
    return bc


def gower(D):
    n = len(D)
    D2 = [[d * d for d in row] for row in D]
    rm = [sum(row) / n for row in D2]
    gm = sum(rm) / n
    return [[-F(1, 2) * (D2[i][j] - rm[i] - rm[j] + gm) for j in range(n)] for i in range(n)]


def community_key(samples, transform, distance):
    ids = list(samples)
    f = dist_fn(transform, distance)
    D = [[f(samples[a], samples[b]) for b in ids] for a in ids]
    B = gower(D)
    lam = np.linalg.eigvalsh(np.array([[float(v) for v in row] for row in B]))[::-1]
    scale = max(abs(lam))
    nonnull = [float(v) for v in lam if abs(v) > 1e-8 * scale]
    trace = sum(B[i][i] for i in range(len(ids)))
    frob = sum(v * v for row in B for v in row)
    div = {}
    for s, x in samples.items():
        p = rel(x)
        div[s] = {"richness": sum(1 for a in x if a > 0), "total": sum(x),
                  "shannon": -sum(float(q) * math.log(float(q)) for q in p if q > 0),
                  "simpson": float(1 - sum(q * q for q in p))}
    return {"ids": ids, "D": D, "B": B, "lam": lam, "nonnull": nonnull, "trace": float(trace), "frob": float(frob), "div": div}


def checks_for(key, *, dims=None, eig=True, diversity=True):
    pairs = {f"{a}|{b}": float(key["D"][i][j]) for i, a in enumerate(key["ids"]) for j, b in enumerate(key["ids"]) if i < j}
    out = [["sample_ids", key["ids"], 0], ["distance_pairs", pairs, 1e-12]]
    if diversity:
        out.append(["diversity_by_id", key["div"], 1e-12])
    if eig:
        neg = sum(1 for v in key["nonnull"] if v < 0)
        out += [["eigenvalues_nonnull_desc", key["nonnull"], 1e-12], ["eigen_trace", key["trace"], 1e-12],
                ["eigen_sumsq", key["frob"], 1e-12], ["negative_count", neg, 0]]
    return out


p01 = taxa_file("c01.dat", SAMPLES)
for fid, transform, distance in [("C01a", "none", "braycurtis"), ("C01b", "relative_abundance", "braycurtis"),
                                 ("C01c", "none", "jaccard")]:
    k = community_key(SAMPLES, transform, distance)
    gaps = [(k["lam"][i] - k["lam"][i + 1]) / k["lam"][0] for i in range(3)]
    add(fid, "community", "analytic",
        f"Hand-computable 4x4: exact rational {distance} ({transform}) distances, plug-in diversity, double-centred spectrum invariants (gaps {np.round(gaps, 4).tolist()})",
        comm_spec(p01, transform, distance, dims=1), {"outcome": "result", "checks": checks_for(k)})

TWO = {"a": [1, 2, 3, 0], "b": [0, 2, 1, 4]}
p = taxa_file("c02.dat", TWO)
d = float(bc(TWO["a"], TWO["b"]))
add("C02", "community", "analytic", "Two samples, BC = 7/13: one positive eigenvalue d^2/2, coordinates +-d/2",
    comm_spec(p, dims=1), {"outcome": "result", "checks": [["distance_pairs", {"a|b": 7 / 13}, 1e-12],
                           ["eigenvalues_nonnull_desc", [d * d / 2], 1e-12], ["abs_axis1", [d / 2, d / 2], 1e-12]]})

TRI = {"a": [3, 0, 0], "b": [0, 5, 0], "c": [0, 0, 2]}
p = taxa_file("c03.dat", TRI, taxa=["t1", "t2", "t3"])
add("C03", "community", "analytic", "Disjoint supports form an equilateral triangle: eigenvalues 1/2, 1/2; G2 = J/2",
    comm_spec(p, dims=2), {"outcome": "result", "checks": [["eigenvalues_nonnull_desc", [0.5, 0.5], 1e-12],
                           ["positive_gram", [[1 / 3 if i == j else -1 / 6 for j in range(3)] for i in range(3)], 1e-12]]})
add("C04", "community", "adversarial", "Equilateral triangle with dimensions=1: axis 1 is not identifiable (zero eigengap); refuse",
    comm_spec(p, dims=1), {"outcome": "refusal"})

add("C05", "community", "adversarial", "relative_abundance before binary Jaccard is rejected",
    comm_spec(p01, "relative_abundance", "jaccard"), {"outcome": "refusal"})
p = write("c06.dat", past_columns(["s1", "s2", "s3"], [("t1", ["0.25", "0.5", "0.1"]), ("t2", ["0.75", "0.5", "0.9"])]))
add("C06", "community", "adversarial", "Proportions declared as counts must be refused (D2)", comm_spec(p, dims=1), {"outcome": "refusal"})
p = write("c07.dat", past_columns(["s1", "s2", "s3"], [("t1", [3, -1, 2]), ("t2", [1, 4, 2])]))
add("C07", "community", "adversarial", "Negative count", comm_spec(p, dims=1), {"outcome": "refusal"})
p = write("c08.dat", past_columns(["s1", "s2", "s3"], [("t1", [3, ".", 2]), ("t2", [1, 4, 2])]))
add("C08", "community", "adversarial", "Missing '.' in a count matrix with missing='error' (D8)", comm_spec(p, dims=1), {"outcome": "refusal"})

EMPTY = dict(SAMPLES, s5=[0, 0, 0, 0])
p = taxa_file("c09.dat", EMPTY)
add("C09", "community", "adversarial", "Empty sample with empty_samples='error' (D7)", comm_spec(p, dims=1), {"outcome": "refusal"})
k = community_key(SAMPLES, "none", "braycurtis")
add("C10", "community", "analytic", "Empty sample with empty_samples='drop': excluded with reason; remainder equals C01a",
    comm_spec(p, dims=1, empty="drop"), {"outcome": "result",
    "checks": checks_for(k) + [["excluded_ids", ["s5"], 0], ["excluded_reasons", ["empty_sample"], 0]]})

p = write("c11.dat", past_columns(["s1", "s2", "s1"], [("t1", [1, 2, 3]), ("t2", [4, 5, 6])]))
add("C11", "community", "adversarial", "Duplicate sample IDs (D9)", comm_spec(p, dims=1), {"outcome": "refusal"})
p = write("c12.dat", past_columns(["s1", "s2", "s3"], [("t1", [1, 2, 3]), ("t1", [4, 5, 6])]))
add("C12", "community", "adversarial", "Duplicate taxon IDs", comm_spec(p, dims=1), {"outcome": "refusal"})
p = write("c13.dat", past_columns(["s1", "s2", "s3"], [("Lingula", [1, 2, 3]), ("lingula", [4, 0, 6]), ("Orthis", [2, 2, 0])]))
add("C13", "community", "adversarial", "Taxon labels differing only by case (D4): must be flagged (warning) or refused, never silent",
    comm_spec(p, dims=1), {"outcome": "refusal_or_warning", "warning": "near_duplicate_labels"})

p = write("c14.dat", (DATA / "c01.dat").read_text() + "t5 0 0 0 0\n")
for fid, transform, distance in [("C14a", "none", "braycurtis"), ("C14b", "none", "jaccard")]:
    k = community_key(SAMPLES, transform, distance)
    add(fid, "community", "metamorphic", f"A taxon absent from every sample leaves {distance} distances, diversity and spectrum unchanged",
        comm_spec(p, transform, distance, dims=1), {"outcome": "result", "checks": checks_for(k)})

SCALED = dict(SAMPLES, s2=[70, 0, 0, 0])
p = taxa_file("c16.dat", SCALED)
k = community_key(SAMPLES, "relative_abundance", "braycurtis")
add("C16", "community", "metamorphic", "Multiplying one sample by 7 leaves relative-abundance BC unchanged",
    comm_spec(p, "relative_abundance", dims=1), {"outcome": "result", "checks": checks_for(k, diversity=False)})

PERM = {s: SAMPLES[s] for s in ["s3", "s1", "s4", "s2"]}
p = taxa_file("c17.dat", PERM)
k = community_key(PERM, "none", "braycurtis")
add("C17", "community", "metamorphic", "Permuting sample columns permutes distances and preserves the spectrum; order follows the input",
    comm_spec(p, dims=1), {"outcome": "result", "checks": checks_for(k)})

p = write("c18.dat", past_columns(TAXA, [(s, v) for s, v in SAMPLES.items()]))
k = community_key(SAMPLES, "none", "braycurtis")
add("C18", "community", "metamorphic", "The transposed file declared samples_by_taxa gives results identical to C01a",
    comm_spec(p, dims=1, orientation="samples_by_taxa"), {"outcome": "result", "checks": checks_for(k)})

NONEUC = {"u1": [0, 5, 6, 0, 0], "u2": [7, 5, 0, 1, 0], "u3": [5, 0, 0, 0, 5], "u4": [0, 1, 0, 0, 5], "u5": [0, 0, 5, 0, 3]}
k = community_key(NONEUC, "none", "braycurtis")
assert any(v < 0 for v in k["nonnull"]), k["nonnull"]
p = taxa_file("c19.dat", NONEUC, taxa=["t1", "t2", "t3", "t4", "t5"])
add("C19", "community", "analytic", f"Non-Euclidean BC: negative eigenvalue(s) {[round(v, 6) for v in k['nonnull'] if v < 0]} reported; spectrum invariants exact",
    comm_spec(p, dims=1), {"outcome": "result", "checks": checks_for(k)})

BIG = {s: [v * 10 ** 9 for v in x] for s, x in SAMPLES.items()}
p = taxa_file("c20.dat", BIG)
kb = community_key(BIG, "none", "braycurtis")
add("C20", "community", "metamorphic", "Scaling every count by 1e9 leaves raw BC, Shannon and Simpson unchanged; totals scale",
    comm_spec(p, dims=1), {"outcome": "result", "checks": checks_for(kb)})

meta_ok = write("c23-meta.csv", "sample_id,site\ns4,D\ns2,B\ns1,A\ns3,C\n")
k = community_key(SAMPLES, "none", "braycurtis")
add("C23", "community", "metamorphic", "Metadata rows in a different order join by ID (D3); results equal C01a",
    comm_spec(p01, dims=1, metadata=meta_ok), {"outcome": "result", "checks": checks_for(k)})
meta_missing = write("c24-meta.csv", "sample_id,site\ns1,A\ns2,B\ns3,C\n")
add("C24", "community", "adversarial", "Metadata lacks one matrix sample: refuse with the ID difference (D3)",
    comm_spec(p01, dims=1, metadata=meta_missing), {"outcome": "refusal"})
meta_extra = write("c24b-meta.csv", "sample_id,site\ns1,A\ns2,B\ns3,C\ns4,D\ns9,Z\n")
add("C24b", "community", "adversarial", "Metadata names a sample absent from the matrix: refuse (D3)",
    comm_spec(p01, dims=1, metadata=meta_extra), {"outcome": "refusal"})
add("C25", "community", "adversarial", "dimensions exceeds the number of positive axes (C01a has 3 at most)",
    comm_spec(p01, dims=4), {"outcome": "refusal"})
add("C26", "community", "adversarial", "Wrong orientation declared with metadata present: taxa t1..t4 would be read as samples; must refuse (D6)",
    comm_spec(p01, dims=1, orientation="samples_by_taxa", metadata=meta_ok), {"outcome": "refusal"})
p = write("c30.dat", past_columns(["s1"], [("t1", [3]), ("t2", [4])]))
add("C30", "community", "adversarial", "A single sample cannot be ordinated", comm_spec(p, dims=1), {"outcome": "refusal"})
p = write("c31.dat", past_columns(["s1", "s2", "s3"], [("t1", [2, 2, 2]), ("t2", [5, 5, 5])]))
add("C31", "community", "adversarial", "All samples identical: no positive axis", comm_spec(p, dims=1), {"outcome": "refusal"})


# ---------------------------------------------------------------- sensitivity
def average_ranks(values):
    order = sorted(range(len(values)), key=lambda i: values[i])
    ranks = [0.0] * len(values)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and values[order[j + 1]] == values[order[i]]:
            j += 1
        for k_ in range(i, j + 1):
            ranks[order[k_]] = (i + j) / 2 + 1
        i = j + 1
    return ranks


def pearson(a, b):
    a, b = np.asarray(a, float), np.asarray(b, float)
    a, b = a - a.mean(), b - b.mean()
    return float(a @ b / math.sqrt((a @ a) * (b @ b)))


def coords(B, k):
    w, v = np.linalg.eigh(np.array([[float(x) for x in row] for row in B]))
    idx = np.argsort(w)[::-1][:k]
    return v[:, idx] * np.sqrt(w[idx])


def procrustes_m2(X, Y):
    X, Y = X - X.mean(0), Y - Y.mean(0)
    X, Y = X / np.linalg.norm(X), Y / np.linalg.norm(Y)
    return float(1 - np.linalg.svd(X.T @ Y, compute_uv=False).sum() ** 2)


k_raw = community_key(SAMPLES, "none", "braycurtis")
k_rel = community_key(SAMPLES, "relative_abundance", "braycurtis")
ids = k_raw["ids"]
upper = [(i, j) for i in range(4) for j in range(i + 1, 4)]
draw = [float(k_raw["D"][i][j]) for i, j in upper]
drel = [float(k_rel["D"][i][j]) for i, j in upper]
totals = [sum(SAMPLES[s]) for s in ids]
bound = [[float(F(abs(totals[i] - totals[j]), totals[i] + totals[j])) for j in range(4)] for i in range(4)]
sens = {"baseline": comm_spec(p01, dims=1), "sensitivity": dict(comm_spec(p01, "relative_abundance", dims=1),
        purpose="Blind fixture: raw versus relative-abundance Bray-Curtis")}
add("S01", "sensitivity", "analytic", "Raw vs relative BC on the 4x4 set: Pearson, Spearman (average ranks), symmetric Procrustes m2 (k=1), total-imbalance bound",
    sens, {"outcome": "result", "checks": [["pearson_distance_correlation", pearson(draw, drel), 1e-12],
           ["spearman_distance_correlation", pearson(average_ranks(draw), average_ranks(drel)), 1e-12],
           ["symmetric_procrustes_m2", procrustes_m2(coords(k_raw["B"], 1), coords(k_rel["B"], 1)), 1e-10],
           ["raw_count_total_imbalance_bound", bound, 1e-12]]})
add("S02", "sensitivity", "adversarial", "Sensitivity arm on different input bytes (counts x1e9) must be refused",
    {"baseline": comm_spec(p01, dims=1), "sensitivity": dict(comm_spec("data/c20.dat", "relative_abundance", dims=1), purpose="x")},
    {"outcome": "refusal"})
add("S03", "sensitivity", "adversarial", "Sensitivity arm also changes dimensions: only transform/distance may change",
    {"baseline": comm_spec(p01, dims=1), "sensitivity": dict(comm_spec(p01, "relative_abundance", dims=2), purpose="x")},
    {"outcome": "refusal"})
add("S04", "sensitivity", "adversarial", "Sensitivity arm identical to baseline: nothing changed",
    {"baseline": comm_spec(p01, dims=1), "sensitivity": dict(comm_spec(p01, dims=1), purpose="x")}, {"outcome": "refusal"})
add("S05", "sensitivity", "adversarial", "Declared baseline fingerprint does not match the baseline run",
    {"baseline": comm_spec(p01, dims=1), "sensitivity": dict(comm_spec(p01, "relative_abundance", dims=1), purpose="x",
     baseline_run="0" * 64)}, {"outcome": "refusal"})

(OUT / "fixtures.json").write_text(json.dumps({"author": "Claude (claude-opus-5-5), interactive session",
    "authored": "2026-10-31", "basis": "Documented specs and public API of Palaeo-Agent at e04b592; keys from definitions, not from palaeo_agent",
    "fixtures": fixtures}, indent=1) + "\n")
print(len(fixtures), "fixtures")
