"""Pilot bank v4: realistic multistep dossiers, matched controls and a disjoint calibration set.

Each item is a small lab dossier: a count or measurement table, sample metadata,
a lab log and the records a real project keeps. task.md states the scientific
question only; dictionary.md describes fields neutrally, with no consequences
or remedies. The fact that decides the handling sits where real data keeps it.
Controls share each trap's structure, scale and innocuous irregularities
(a low-yield sample counted in full, never-observed taxa, unordered or surplus
metadata rows), with the pitfall's evidence resolved.

Keys are computed by parsing the written files with the warranted handling
(`reference`), never from generator internals. Each key carries failure
signatures from plausible wrong handlings, accepted alternative results where
more than one handling is defensible, a written analysis specification for the
independent implementation witness, and a replay perturbation verified to move
the key.

    uv run python evaluation/pilot/build_bank_v4.py     # writes items-v4/ and calibration-v4/
"""

import csv
from fractions import Fraction
import hashlib
import io
from itertools import combinations
import json
import math
from pathlib import Path
import random
import shutil

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
TOLERANCE = {"abs": 1e-4, "rel": 1e-4}
BANK_VERSION = "pilot-v4"
REPORT = "Write `answer.json` following `answer.schema.json`."

PLANKTIC = ["Globigerina bulloides", "Globigerina falconensis", "Globigerinoides ruber", "Globigerinoides conglobatus",
            "Trilobatus sacculifer", "Orbulina universa", "Neogloboquadrina incompta", "Neogloboquadrina pachyderma",
            "Neogloboquadrina dutertrei", "Globorotalia inflata", "Globorotalia truncatulinoides",
            "Globorotalia menardii", "Globorotalia scitula", "Globorotalia hirsuta", "Globigerinita glutinata",
            "Globigerinita uvula", "Turborotalita quinqueloba", "Pulleniatina obliquiloculata",
            "Globigerinella siphonifera", "Globigerinella calida", "Hastigerina pelagica", "Candeina nitida",
            "Beella digitata", "Globoturborotalita rubescens", "Globoturborotalita tenella", "Berggrenia pumilio",
            "Tenuitella iota", "Sphaeroidinella dehiscens"]
BENTHIC = ["Cibicidoides wuellerstorfi", "Cibicidoides pachyderma", "Uvigerina peregrina", "Uvigerina mediterranea",
           "Bulimina marginata", "Bulimina aculeata", "Melonis barleeanum", "Melonis pompilioides",
           "Hoeglundina elegans", "Pyrgo murrhina", "Pyrgo depressa", "Globobulimina affinis", "Oridorsalis umbonatus",
           "Gyroidina soldanii", "Pullenia bulloides", "Pullenia quinqueloba", "Epistominella exigua",
           "Nonionella turgida", "Bolivina spathulata", "Bolivina robusta", "Cassidulina laevigata",
           "Cassidulina crassa", "Elphidium excavatum", "Ammonia beccarii", "Quinqueloculina seminula",
           "Textularia agglutinans"]
BENIGN = ["counted in full", "counted in full", "counted in full", "split 1/1; counted in full",
          "picked by second analyst; cross-checked", "slide re-labelled after drying; counted in full",
          "sieved twice (clay); counted in full", "photographed before picking", "residue archived (store A)",
          "counted in full; two broken tests not identifiable", "re-counted after audit; counts unchanged"]


# ---------- exact definitions ----------

def bc(a, b):
    total = sum(a) + sum(b)
    return Fraction(sum(abs(Fraction(x) - Fraction(y)) for x, y in zip(a, b))) / total


def relative(row):
    total = sum(row)
    return [Fraction(x) / total for x in row]


def mean_pairwise(rows):
    pairs = list(combinations(rows, 2))
    return sum(bc(a, b) for a, b in pairs) / len(pairs)


def permanova(rows, groups):
    n, labels = len(rows), sorted(set(groups))
    d2 = {(i, j): bc(rows[i], rows[j]) ** 2 for i, j in combinations(range(n), 2)}
    ss_t = sum(d2.values()) / n
    ss_w = sum(sum(v for (i, j), v in d2.items() if groups[i] == groups[j] == g) / groups.count(g) for g in labels)
    a = len(labels)
    return {"pseudo_f": float(((ss_t - ss_w) / (a - 1)) / (ss_w / (n - a))), "r_squared": float((ss_t - ss_w) / ss_t)}


def shannon(row):
    total = sum(row)
    return -math.fsum(float(Fraction(x) / total) * math.log(Fraction(x) / total) for x in row if x)


def rma_log(x, y):
    lx, ly = [math.log10(v) for v in x], [math.log10(v) for v in y]
    n = len(lx)
    mx, my = math.fsum(lx) / n, math.fsum(ly) / n
    sxx = math.fsum((v - mx) ** 2 for v in lx)
    syy = math.fsum((v - my) ** 2 for v in ly)
    sxy = math.fsum((a - mx) * (b - my) for a, b in zip(lx, ly))
    slope = math.copysign(math.sqrt(syy / sxx), sxy)
    return {"slope": slope, "intercept": my - slope * mx, "n": n}


# ---------- files ----------

def tsv(header, rows):
    return "\t".join(header) + "\n" + "".join("\t".join(map(str, r)) + "\n" for r in rows)


def csv_text(header, rows):
    stream = io.StringIO()
    writer = csv.writer(stream, lineterminator="\n")
    writer.writerow(header)
    writer.writerows(rows)
    return stream.getvalue()


def read_counts(path, orientation="samples_by_taxa", number=int):
    rows = [line.split("\t") for line in Path(path).read_text().splitlines() if line.strip()]
    header, body = rows[0][1:], rows[1:]
    labels, values = [r[0] for r in body], [[number(v) for v in r[1:]] for r in body]
    if orientation == "taxa_by_samples":
        return header, labels, [list(c) for c in zip(*values)]
    return labels, header, values


def read_csv(path):
    return list(csv.DictReader(Path(path).open()))


# ---------- generators ----------

def community(rng, n_taxa, groups, totals=(180, 420), strength=1.0, rare=2):
    """Counts per sample from group-specific profiles; `rare` taxa are never observed."""
    base = [rng.uniform(0.2, 3) for _ in range(n_taxa - rare)]
    profiles = {g: [b * math.exp(strength * rng.gauss(0, 0.7)) for b in base] for g in sorted(set(groups))}
    rows = []
    for group in groups:
        weights = [w * math.exp(rng.gauss(0, 0.35)) for w in profiles[group]]
        counts = [0] * len(weights)
        for index in rng.choices(range(len(weights)), weights=weights, k=rng.randint(*totals)):
            counts[index] += 1
        rows.append(counts + [0] * rare)
    return rows


def taxa(rng, n, pool=None):
    names = rng.sample(pool or PLANKTIC + BENTHIC, n)
    return names


def low_yield(rng, row):
    """A real sample with few specimens: thinned in proportion."""
    keep = rng.randint(38, 55)
    flat = [i for i, c in enumerate(row) for _ in range(c)]
    out = [0] * len(row)
    for index in rng.sample(flat, keep):
        out[index] += 1
    return out


def lab_log(rng, samples, special, year=2025):
    rows = []
    for s in samples:
        remark = special.get(s, rng.choice(BENIGN))
        rows.append([s, f"{year}-{rng.randint(1, 12):02d}-{rng.randint(1, 28):02d}", rng.choice(["AK", "JM", "RT"]), remark])
    rng.shuffle(rows)
    return csv_text(["sample_id", "processed", "analyst", "remark"], rows)


def item(**fields):
    defaults = {"integer": [], "failures": [], "tokens": [], "exclusions": [], "out_of_scope": [], "alternatives": [],
                "disclosure": [], "equivalents": [], "alternative_results": []}
    return defaults | fields


# Each family returns item(...) with: family, cls, stratum, task, dictionary, files, reference (materials -> results),
# failures (list of (name, function)), perturbation, specification, witness, tokens, and optional extras.

def p01_uncounted(cls, seed, n_taxa=None, n_samples=None):
    rng = random.Random(seed)
    n_taxa, n_samples = n_taxa or rng.randint(28, 40), n_samples or rng.randint(20, 28)
    names = taxa(rng, n_taxa)
    samples = [f"KC{i:02d}" for i in range(1, n_samples + 1)]
    rows = community(rng, n_taxa, ["x"] * n_samples, strength=0.6)
    lost, thin = rng.sample(samples[2:-2], 2)
    rows[samples.index(thin)] = low_yield(rng, rows[samples.index(thin)])
    special = {thin: "low yield; counted in full"}
    if cls == "trap":
        rows[samples.index(lost)] = [0] * n_taxa
        special[lost] = "residue not recovered after store B flood; no picking"
    data = [[name] + [rows[j][i] for j in range(n_samples)] for i, name in enumerate(names)]
    files = {"counts.tsv": tsv(["taxon"] + samples, data), "lab_log.csv": lab_log(rng, samples, special)}

    def reference(m, drop_zero=True, drop=()):
        smp, _, vals = read_counts(m / "counts.tsv", "taxa_by_samples")
        kept = [v for s, v in zip(smp, vals) if (sum(v) > 0 or not drop_zero) and s not in drop]
        return {"mean_bray_curtis": float(mean_pairwise(kept)), "n_samples": len(kept)}

    failures = [("low_yield_dropped", lambda m: reference(m, drop=(thin,)))]
    if cls == "trap":
        failures.append(("zeros_as_sample", lambda m: reference(m, drop_zero=False)))
    return item(family="P01", cls=cls, stratum="toolkit", files=files, reference=reference, failures=failures,
                integer=["n_samples"], exclusions=[lost] if cls == "trap" else [],
                tokens=[["not recovered", "flood", "uncounted", "not counted", "no picking", "zeros", lost]] if cls == "trap" else [],
                perturbation={"file": "counts.tsv", "kind": "add_row", "match": names[0], "value": 3},
                task=("# Faunal turnover along the Kerguelen transect\n\nSummarise how much assemblages differ between "
                      "samples as the mean Bray–Curtis dissimilarity over all pairs of sample assemblages, on raw "
                      "counts.\n\nReport in `results`: `mean_bray_curtis` and `n_samples` (the number of samples in "
                      f"the calculation).\n\n{REPORT}\n"),
                dictionary=("# Kerguelen transect foraminifera\n\n"
                            "- `counts.tsv`: tab-separated export from the laboratory database. The first column "
                            "names the taxon; each further column is one sample (KC01–KC%02d, ordered along the "
                            "transect). Cells are numbers of specimens picked from the >150 µm fraction.\n"
                            "- `lab_log.csv`: one row per sample from the processing log: `sample_id`, `processed` "
                            "(date), `analyst` (initials) and `remark` (free text written at the bench).\n"
                            % n_samples),
                specification=("Read counts.tsv (taxa as rows, samples as columns). Exclude any sample whose column is "
                               "all zero. Compute Bray–Curtis dissimilarity on raw counts for every pair of remaining "
                               "samples and report the mean, and the number of samples used."),
                witness=(f"The log records that {lost}'s residue was not recovered and never picked, and its column "
                         "is all zeros: it is an export placeholder, not an assemblage, so it is excluded. "
                         f"{thin} is a genuine low-yield sample counted in full and stays."
                         if cls == "trap" else f"Every sample was picked; {thin} is low-yield but counted in full."))


def p02_id_formats(cls, seed, n_taxa=None, n_samples=None):
    rng = random.Random(seed)
    n_taxa, n_samples = n_taxa or rng.randint(26, 36), n_samples or rng.randint(20, 26)
    names = taxa(rng, n_taxa)
    samples = [f"PB{i:02d}" for i in range(1, n_samples + 1)]
    zones = [rng.choice("AB") for _ in samples]
    zones[0], zones[1] = "A", "B"
    rows = community(rng, n_taxa, zones, strength=0.9)
    legs = ["1" if i < n_samples * 0.65 else "2" for i in range(n_samples)]
    logged = {s: (f"PB-{s[2:]}" if cls == "trap" and leg == "2" else s) for s, leg in zip(samples, legs)}
    stations = [[logged[s], z, rng.randint(250, 1900), leg] for s, z, leg in zip(samples, zones, legs)]
    stations += [[f"PB{n_samples + k:02d}", rng.choice("AB"), rng.randint(250, 1900), "2"] for k in (1, 2)]
    rng.shuffle(stations)
    files = {"counts.tsv": tsv(["sample"] + names, [[s] + r for s, r in zip(samples, rows)]),
             "stations.csv": csv_text(["station_id", "zone", "water_depth_m", "leg"], stations),
             "lab_log.csv": lab_log(rng, samples, {})}

    def reference(m, normalise=True, by_position=False):
        smp, _, vals = read_counts(m / "counts.tsv")
        meta = read_csv(m / "stations.csv")
        if by_position:
            groups = [r["zone"] for r in meta[:len(smp)]]
            return permanova(vals, groups) | {"n": len(smp)}
        key = (lambda x: x.replace("-", "")) if normalise else (lambda x: x)
        zone = {key(r["station_id"]): r["zone"] for r in meta}
        kept = [(v, zone[s]) for s, v in zip(smp, vals) if s in zone]
        return permanova([v for v, _ in kept], [g for _, g in kept]) | {"n": len(kept)}

    failures = [("join_by_position", lambda m: reference(m, by_position=True))]
    if cls == "trap":
        failures.append(("exact_join_drops_leg2", lambda m: reference(m, normalise=False)))
    return item(family="P02", cls=cls, stratum="toolkit", files=files, reference=reference, failures=failures,
                integer=["n"], perturbation={"file": "counts.tsv", "kind": "add_row", "match": samples[3], "value": 7},
                tokens=[["PB-", "hyphen", "format", "leg 2", "not match", "unmatched", "normalis", "normaliz"]] if cls == "trap" else [],
                task=("# Zone contrast on the Pelotas slope\n\nTest whether assemblage composition differs between "
                      "the two depositional zones, with a one-way PERMANOVA on Bray–Curtis dissimilarities of raw "
                      "counts, using every counted sample.\n\nReport in `results`: `pseudo_f`, `r_squared` and `n` "
                      f"(samples in the test).\n\n{REPORT}\n"),
                dictionary=("# Pelotas slope foraminifera\n\n"
                            "- `counts.tsv`: tab-separated; one row per counted sample (`sample`), one column per taxon; "
                            "specimen counts.\n"
                            "- `stations.csv`: the station list compiled from both cruise legs: `station_id` as written "
                            "in that leg's station log, `zone` (A: upper slope, B: lower slope, assigned from "
                            "sedimentology), `water_depth_m`, `leg`. Stations were placed at random within zones. Some "
                            "stations yielded no sample.\n"
                            "- `lab_log.csv`: processing log (`sample_id`, `processed`, `analyst`, `remark`).\n"),
                specification=("Join counts.tsv rows to stations.csv by station ID, treating 'PB-07' and 'PB07' as the "
                               "same ID (remove the hyphen). Ignore stations with no counts row. Run one-way PERMANOVA "
                               "(Bray–Curtis on raw counts) with zone as the factor over all counted samples; report "
                               "pseudo-F, R² and n."),
                witness=("Leg-2 station IDs carry a hyphen (PB-07) where the counts use PB07; the numbers are unique "
                         "and identical, so they are the same stations. An exact join silently loses the leg-2 samples."
                         if cls == "trap" else "Station IDs match the counts exactly; two stations have no sample."))


def p03_percent_rows(cls, seed, n_taxa=None, n_samples=None):
    rng = random.Random(seed)
    n_taxa, n_samples = n_taxa or rng.randint(25, 34), n_samples or rng.randint(20, 26)
    names = taxa(rng, n_taxa)
    samples = [f"SR{i:03d}" for i in rng.sample(range(100, 400), n_samples)]
    rows = community(rng, n_taxa, ["x"] * n_samples, strength=0.7)
    campaigns = ["1998" if i % 3 == 0 else "2024" for i in range(n_samples)]
    thin = samples[1]
    rows[1] = low_yield(rng, rows[1])
    table, meta = [], []
    for s, r, c in zip(samples, rows, campaigns):
        n = sum(r)
        percent = cls == "trap" and c == "1998"
        table.append([s] + ([f"{100 * v / n:.2f}" for v in r] if percent else r))
        meta.append([s, c, "relative (%)" if percent else "count", n,
                     "published table (Rivera 1999), counts not archived" if percent else "this study"])
    rng.shuffle(meta)
    files = {"counts.tsv": tsv(["sample"] + names, table),
             "samples.csv": csv_text(["sample_id", "campaign", "value_type", "n_counted", "source"], meta),
             "lab_log.csv": lab_log(rng, [s for s, c in zip(samples, campaigns) if not (cls == "trap" and c == "1998")],
                                    {thin: "low yield; counted in full"})}

    def reference(m, convert=True, drop_percent=False, transform="raw"):
        smp, _, vals = read_counts(m / "counts.tsv", number=lambda v: Fraction(v))
        info = {r["sample_id"]: r for r in read_csv(m / "samples.csv")}
        out = []
        for s, v in zip(smp, vals):
            if info[s]["value_type"] != "count":
                if drop_percent:
                    continue
                if convert:
                    n = int(info[s]["n_counted"])
                    v = [Fraction(round(x * n / 100)) for x in v]
            out.append(relative(v) if transform == "relative" else v)
        return {"mean_bray_curtis": float(mean_pairwise(out))}

    failures = []
    if cls == "trap":
        failures = [("percent_as_counts", lambda m: reference(m, convert=False)),
                    ("percent_rows_dropped", lambda m: reference(m, drop_percent=True))]
    count_row = next(s for s, c in zip(samples, campaigns) if c == "2024" and s != thin)
    return item(family="P03", cls=cls, stratum="toolkit", files=files, reference=reference, failures=failures,
                perturbation={"file": "counts.tsv", "kind": "add_row", "match": count_row, "value": 4},
                tokens=[["percent", "relative", "%", "n_counted", "reconstruct", "convert"]] if cls == "trap" else [],
                task=("# Similarity of São Roque shelf assemblages\n\nSummarise between-sample dissimilarity as the "
                      "mean Bray–Curtis dissimilarity over all pairs of samples, computed on raw specimen counts.\n\n"
                      f"Report in `results`: `mean_bray_curtis`.\n\n{REPORT}\n"),
                dictionary=("# São Roque shelf foraminifera, two campaigns\n\n"
                            "- `counts.tsv`: tab-separated; one row per sample, one column per taxon.\n"
                            "- `samples.csv`: `sample_id`, `campaign`, `value_type` (how the row's values are "
                            "expressed), `n_counted` (specimens identified in the sample), `source`.\n"
                            "- `lab_log.csv`: processing log for samples handled in this study's laboratory.\n"),
                specification=("Use counts.tsv. For rows whose samples.csv value_type is 'relative (%)', convert to "
                               "counts as round(value × n_counted / 100). Compute raw-count Bray–Curtis for all sample "
                               "pairs and report the mean."),
                witness=("The 1998 rows are percentages from a published table, as samples.csv states, with n_counted "
                         "given; raw counts are recovered exactly as percent × n / 100, and percentages are not counts."
                         if cls == "trap" else "All rows are counts from this study."))


SMALL = 0.3


def p04_mesh(cls, seed, n_taxa=None, n_cores=None):
    rng = random.Random(seed)
    n_taxa, n_cores = n_taxa or rng.randint(24, 28), n_cores or rng.randint(18, 24)
    names = taxa(rng, n_taxa, PLANKTIC)
    small = set(rng.sample(names[:-2], round(SMALL * n_taxa)))
    cores = [f"GB{i:02d}" for i in range(1, n_cores + 1)]
    campaign = ["2017" if i % 2 == 0 else "2021" for i in range(n_cores)]
    rows = community(rng, n_taxa, campaign, strength=0.25)
    if cls == "trap":
        for r, c in zip(rows, campaign):
            if c == "2017":
                for i, name in enumerate(names):
                    if name in small:
                        r[i] = 0
    data = [[name] + [rows[j][i] for j in range(n_cores)] for i, name in enumerate(names)]
    mesh = {"2017": "150" if cls == "trap" else "63", "2021": "63"}
    files = {"counts.tsv": tsv(["taxon"] + cores, data),
             "cores.csv": csv_text(["core_id", "campaign", "latitude", "longitude"],
                                   [[c, k, f"-{rng.uniform(40, 42):.3f}", f"{rng.uniform(146, 148):.3f}"]
                                    for c, k in zip(cores, campaign)]),
             "campaigns.csv": csv_text(["campaign", "vessel", "sieve_mesh_um", "picking"],
                                       [["2017", "RV Aurora", mesh["2017"], "all specimens retained on the sieve"],
                                        ["2021", "RV Investigator", mesh["2021"], "all specimens retained on the sieve"]]),
             "taxa.csv": csv_text(["taxon", "adult_test_size"],
                                  [[n, "63–150 µm" if n in small else ">150 µm"] for n in names])}

    def reference(m, restrict=True):
        smp, tx, vals = read_counts(m / "counts.tsv", "taxa_by_samples")
        camp = {r["core_id"]: r["campaign"] for r in read_csv(m / "cores.csv")}
        meshes = {r["campaign"]: int(r["sieve_mesh_um"]) for r in read_csv(m / "campaigns.csv")}
        sizes = {r["taxon"]: r["adult_test_size"] for r in read_csv(m / "taxa.csv")}
        coarse = max(meshes.values())
        keep = [i for i, t in enumerate(tx) if not restrict or coarse <= 63 or sizes[t] == ">150 µm"]
        out = {}
        for year in ("2017", "2021"):
            values = [shannon([v[i] for i in keep]) for s, v in zip(smp, vals) if camp[s] == year]
            out[f"shannon_mean_{year}"] = math.fsum(values) / len(values)
        return out

    failures = [("all_taxa_both_campaigns", lambda m: reference(m, restrict=False))] if cls == "trap" else []
    return item(family="P04", cls=cls, stratum="toolkit", files=files, reference=reference, failures=failures,
                perturbation={"file": "counts.tsv", "kind": "add_row",
                              "match": next(n for n in names if n not in small), "value": 6},
                tokens=[["150", "mesh", "sieve", "size fraction", "63"]] if cls == "trap" else [],
                disclosure=[[">150", "150 µm", "coarse", "large", "comparable"]] if cls == "trap" else [],
                alternatives=[{"status": "stopped", "issue_tokens": [["mesh", "sieve", "150", "size fraction"]]}]
                if cls == "trap" else [],
                task=("# Diversity change on the Tasman slope\n\nCompare planktonic foraminiferal diversity between "
                      "the 2017 and 2021 coring campaigns: the mean, over cores, of each core's Shannon diversity "
                      "(natural logarithm).\n\nReport in `results`: `shannon_mean_2017` and `shannon_mean_2021`.\n\n"
                      f"{REPORT}\n"),
                dictionary=("# Tasman slope core-top foraminifera\n\n"
                            "- `counts.tsv`: tab-separated; taxa as rows, cores as columns; specimen counts.\n"
                            "- `cores.csv`: `core_id`, `campaign`, position.\n"
                            "- `campaigns.csv`: per campaign, `vessel`, `sieve_mesh_um` (mesh used to wash the "
                            "sediment) and `picking`.\n"
                            "- `taxa.csv`: `adult_test_size` for each taxon, from the regional atlas.\n"),
                specification=("If the campaigns used different sieve meshes, restrict both campaigns to taxa whose "
                               "adult_test_size is '>150 µm' when the coarser mesh is 150 µm. Compute Shannon (natural "
                               "log) per core on the retained taxa and report the mean per campaign."),
                witness=("2017 sediments were washed on a 150 µm mesh, so taxa whose adults are 63–150 µm could not "
                         "be retained; their zeros in 2017 are not absences. Diversity is comparable only on the "
                         ">150 µm taxa, a restriction the answer must state; stopping with the reason is also acceptable."
                         if cls == "trap" else "Both campaigns used a 63 µm mesh; all taxa are comparable."))


SYNONYMS = [("Globigerinoides sacculifer", "Trilobatus sacculifer"),
            ("Globigerinoides tenellus", "Globoturborotalita tenella")]
VARIANTS = [("Neogloboquadrina pachyderma (sinistral)", "Neogloboquadrina pachyderma"),
            ("Neogloboquadrina pachyderma (dextral)", "Neogloboquadrina incompta")]


def p05_crosswalk(cls, seed, n_taxa=None, n_samples=None):
    rng = random.Random(seed)
    n_taxa, n_samples = n_taxa or rng.randint(24, 26), n_samples or rng.randint(20, 26)
    accepted_pool = [p for p in PLANKTIC if p not in {a for _, a in SYNONYMS + VARIANTS}]
    base = rng.sample(accepted_pool, n_taxa - 4) + [a for _, a in SYNONYMS]
    recorded = base + [r for r, _ in VARIANTS]
    rng.shuffle(recorded)
    crosswalk = {n: n for n in base} | {r: a for r, a in VARIANTS}
    samples = [f"AT{i:02d}" for i in range(1, n_samples + 1)]
    labs = ["Hobart" if i % 2 else "Bremen" for i in range(n_samples)]
    rows = community(rng, len(recorded), ["x"] * n_samples, strength=0.6, rare=0)
    columns = list(recorded)
    if cls == "trap":
        for r_name, a_name in SYNONYMS:
            columns.append(r_name)
            crosswalk[r_name] = a_name
            j = recorded.index(a_name)
            for row, lab in zip(rows, labs):
                if lab == "Bremen":
                    row.append(row[j])
                    row[j] = 0
                else:
                    row.append(0)
    else:
        for extra in rng.sample([p for p in accepted_pool if p not in recorded], 2):
            columns.append(extra)
            crosswalk[extra] = extra
            for row in rows:
                row.append(rng.randint(0, 6))
    order = list(range(len(columns)))
    rng.shuffle(order)
    columns = [columns[i] for i in order]
    rows = [[r[i] for i in order] for r in rows]
    thin = samples[2]
    rows[2] = low_yield(rng, rows[2])
    walk = [[k, v, "WoRMS 2025-10" if k != v else ""] for k, v in sorted(crosswalk.items())]
    files = {"counts.tsv": tsv(["sample"] + columns, [[s] + r for s, r in zip(samples, rows)]),
             "taxonomy.csv": csv_text(["name_as_recorded", "accepted_name", "checked_against"], walk),
             "samples.csv": csv_text(["sample_id", "counting_lab", "water_depth_m"],
                                     [[s, lab, rng.randint(900, 3200)] for s, lab in zip(samples, labs)]),
             "lab_log.csv": lab_log(rng, samples, {thin: "low yield; counted in full"})}

    def reference(m, merge=True, merge_variants=False):
        smp, tx, vals = read_counts(m / "counts.tsv")
        walk = {r["name_as_recorded"]: r["accepted_name"] for r in read_csv(m / "taxonomy.csv")}
        if merge_variants:
            tx = [t.split(" (")[0] for t in tx]
        target = [walk.get(t, t) if merge else t for t in tx]
        names = sorted(set(target))
        merged = [[sum(v for v, t in zip(row, target) if t == n) for n in names] for row in vals]
        present = [n for i, n in enumerate(names) if any(r[i] for r in merged)]
        return {"richness": len(present), "mean_bray_curtis": float(mean_pairwise(merged))}

    failures = [("variants_merged", lambda m: reference(m, merge_variants=True))]
    if cls == "trap":
        failures.append(("synonyms_unmerged", lambda m: reference(m, merge=False)))
    return item(family="P05", cls=cls, stratum="toolkit", files=files, reference=reference, failures=failures,
                integer=["richness"], perturbation={"file": "counts.tsv", "kind": "add_row", "match": samples[5], "value": 5},
                tokens=[["synonym", "accepted", "crosswalk", "taxonomy.csv", "same species", "incompta", "sacculifer"]]
                if cls == "trap" else [],
                task=("# Atlantis Bank assemblages\n\nReport species richness (number of species with at least one "
                      "specimen across the data set) and the mean Bray–Curtis dissimilarity over all pairs of samples "
                      "on raw counts, at species level under current taxonomy.\n\nReport in `results`: `richness` and "
                      f"`mean_bray_curtis`.\n\n{REPORT}\n"),
                dictionary=("# Atlantis Bank planktonic foraminifera, two counting laboratories\n\n"
                            "- `counts.tsv`: tab-separated; one row per sample, one column per name as recorded by the "
                            "counting laboratory.\n"
                            "- `taxonomy.csv`: every recorded name with its `accepted_name` under current taxonomy.\n"
                            "- `samples.csv`: `sample_id`, `counting_lab`, `water_depth_m`.\n"
                            "- `lab_log.csv`: processing log.\n"),
                specification=("Rename each counts.tsv column to its taxonomy.csv accepted_name (exact recorded string) and sum columns that "
                               "share an accepted name. Richness is the number of accepted names with a nonzero total. "
                               "Mean Bray–Curtis on the merged raw counts over all sample pairs."),
                witness=("The Bremen laboratory recorded two species under older names; taxonomy.csv maps each to an "
                         "accepted name already used by Hobart, so the columns are one species and are summed. The "
                         "sinistral and dextral pachyderma columns map to two distinct accepted species "
                         "(N. pachyderma, N. incompta) and stay separate."
                         if cls == "trap" else "Every recorded name maps to its own accepted name; nothing merges."))


def p06_aliquots(cls, seed, n_taxa=None, n_cores=None):
    rng = random.Random(seed)
    n_taxa, n_cores = n_taxa or rng.randint(22, 26), n_cores or rng.randint(10, 14)
    names = taxa(rng, n_taxa, BENTHIC)
    cores = [f"MC{i:02d}" for i in range(1, n_cores + 1)]
    zones = ["inner" if i % 2 == 0 else "outer" for i in range(n_cores)]
    core_rows = community(rng, n_taxa, zones, totals=(400, 700), strength=0.8)
    lab_numbers, register, rows = [], [], []
    number = rng.randint(4100, 4300)
    for core, row in zip(cores, core_rows):
        parts = (rng.choice([2, 3]) if cls == "trap" and rng.random() < 0.6 else 1)
        flat = [i for i, c in enumerate(row) for _ in range(c)]
        rng.shuffle(flat)
        cuts = sorted(rng.sample(range(1, len(flat)), parts - 1))
        for k, chunk in enumerate(zip([0] + cuts, cuts + [len(flat)])):
            number += rng.randint(1, 9)
            values = [0] * n_taxa
            for index in flat[chunk[0]:chunk[1]]:
                values[index] += 1
            lab = f"L{number}"
            lab_numbers.append(lab)
            rows.append(values)
            register.append([lab, core, "abcd"[k] if parts > 1 else "", rng.choice(["2025-03", "2025-04", "2025-05"])])
    rng.shuffle(register)
    files = {"counts.tsv": tsv(["lab_number"] + names, [[l] + r for l, r in zip(lab_numbers, rows)]),
             "register.csv": csv_text(["lab_number", "core_id", "split", "batch"], register),
             "cores.csv": csv_text(["core_id", "zone", "site_spacing_km", "water_depth_m"],
                                   [[c, z, rng.randint(3, 9), rng.randint(40, 140)] for c, z in zip(cores, zones)]),
             "lab_log.csv": lab_log(rng, lab_numbers, {})}

    def reference(m, pool="sum", raw=False):
        labs, _, vals = read_counts(m / "counts.tsv")
        core_of = {r["lab_number"]: r["core_id"] for r in read_csv(m / "register.csv")}
        zone = {r["core_id"]: r["zone"] for r in read_csv(m / "cores.csv")}
        if pool == "none":
            return permanova([relative(v) for v in vals], [zone[core_of[l]] for l in labs]) | {"n": len(labs)}
        grouped = {}
        for l, v in zip(labs, vals):
            grouped.setdefault(core_of[l], []).append(v)
        ids = sorted(grouped)
        if pool == "sum":
            units = [(lambda u: u if raw else relative(u))([sum(c) for c in zip(*grouped[i])]) for i in ids]
        else:
            units = [[sum(c) / len(c) for c in zip(*[relative(v) for v in grouped[i]])] for i in ids]
        return permanova(units, [zone[i] for i in ids]) | {"n": len(ids)}

    alternatives = [{"name": "mean_of_aliquot_proportions", "results": {"pool": "mean"},
                     "reason": "Averaging aliquot relative abundances per core is also a defensible core-level pooling."}]
    failures = [("aliquots_as_units", lambda m: reference(m, pool="none"))] if cls == "trap" else []
    return item(family="P06", cls=cls, stratum="toolkit", files=files, reference=reference, failures=failures,
                integer=["n"], alternative_results=alternatives if cls == "trap" else [],
                perturbation={"file": "counts.tsv", "kind": "add_row", "match": lab_numbers[0], "value": 9},
                tokens=[["aliquot", "split", "pseudorepl", "same core", "pool", "register"]] if cls == "trap" else [],
                task=("# Inner versus outer shelf, Storm Bay\n\nTest whether benthic assemblage composition differs "
                      "between inner- and outer-shelf cores with a one-way PERMANOVA on Bray–Curtis dissimilarities of "
                      "relative abundances.\n\nReport in `results`: `pseudo_f`, `r_squared` and `n` (sampling units in "
                      f"the test).\n\n{REPORT}\n"),
                dictionary=("# Storm Bay benthic foraminifera\n\n"
                            "- `counts.tsv`: tab-separated; one row per laboratory number, one column per taxon.\n"
                            "- `register.csv`: the sample register: `lab_number`, the `core_id` it came from, `split` "
                            "(letter of the residue split processed under that number, blank if unsplit) and `batch`.\n"
                            "- `cores.csv`: one row per core: `zone`, `site_spacing_km` (distance to the nearest other "
                            "site), `water_depth_m`. Each core was taken at its own site.\n"
                            "- `lab_log.csv`: processing log by laboratory number.\n"),
                specification=("Map each lab_number to its core via register.csv and sum the counts of a core's lab "
                               "numbers. Convert each core to relative abundances and run one-way PERMANOVA "
                               "(Bray–Curtis) with zone as the factor, cores as units; report pseudo-F, R² and n."),
                witness=("Several cores were split and processed under two or three laboratory numbers; the splits "
                         "are subsamples of one core at one site, so the core is the sampling unit and its splits are "
                         "pooled. Treating splits as units inflates n." if cls == "trap"
                         else "Each core has exactly one laboratory number; cores are the units."))


def p07_observer_units(cls, seed, n=None):
    rng = random.Random(seed)
    n = n or rng.randint(70, 110)
    observers = {"KT": ("ruler", "cm"), "RM": ("digital caliper, 0.01 mm", "mm"), "AS": ("dial caliper, 0.1 mm", "mm"),
                 "JB": ("dial caliper, 0.1 mm", "mm")}
    if cls == "control":
        observers["KT"] = ("dial caliper, 0.1 mm", "mm")
    rows = []
    for i in range(n):
        length = math.exp(rng.gauss(math.log(24), 0.35))
        width = 0.62 * length ** 0.93 * math.exp(rng.gauss(0, 0.06))
        obs = rng.choice(list(observers))
        scale, digits = (0.1, 1) if observers[obs][1] == "cm" else (1, 2 if obs == "RM" else 1)
        rows.append([f"D{i + 1:03d}", rng.choice(["Ross", "Maydena", "Florentine"]), obs,
                     f"{length * scale:.{digits}f}", f"{width * scale:.{digits}f}"])
    files = {"shells.csv": csv_text(["specimen", "locality", "observer", "length", "width"], rows),
             "observers.csv": csv_text(["observer", "instrument", "unit_recorded", "season"],
                                       [[k, v[0], v[1], rng.choice(["2023", "2024"])] for k, v in observers.items()])}

    def reference(m, convert=True, extra_cm=()):
        unit = {r["observer"]: ("cm" if r["observer"] in extra_cm else r["unit_recorded"])
                for r in read_csv(m / "observers.csv")}
        x, y = [], []
        for r in read_csv(m / "shells.csv"):
            f = 10.0 if convert and unit[r["observer"]] == "cm" else 1.0
            x.append(float(r["length"]) * f)
            y.append(float(r["width"]) * f)
        return rma_log(x, y) | {"mean_length_mm": math.fsum(x) / len(x)}

    failures = [("cm_as_mm", lambda m: reference(m, convert=False))] if cls == "trap" else []
    return item(family="P07", cls=cls, stratum="other", files=files, reference=reference, failures=failures,
                integer=["n"], perturbation={"file": "shells.csv", "kind": "scale_column", "match": "length", "value": 1.05},
                tokens=[["cm", "centimet", "unit", "KT", "ruler", "convert"]] if cls == "trap" else [],
                task=("# Dielasma allometry\n\nEstimate the allometry of shell width on shell length as a "
                      "reduced-major-axis regression of log10(width) on log10(length), with lengths in millimetres.\n\n"
                      "Report in `results`: `slope`, `intercept`, `n` and `mean_length_mm` (mean shell length, mm).\n\n"
                      f"{REPORT}\n"),
                dictionary=("# Dielasma shell measurements\n\n"
                            "- `shells.csv`: one row per specimen: `specimen`, `locality`, `observer` (initials), "
                            "`length` and `width` as recorded.\n"
                            "- `observers.csv`: per observer, the `instrument`, the `unit_recorded` and the `season`.\n"),
                specification=("Convert lengths and widths recorded by observers whose unit_recorded is 'cm' to mm "
                               "(×10). Fit RMA of log10(width) on log10(length) over all specimens; report slope, "
                               "intercept, n and mean length in mm."),
                witness=("Observer KT recorded with a ruler in centimetres (observers.csv); those values are ×10 "
                         "smaller and must be converted before pooling." if cls == "trap"
                         else "Every observer recorded in millimetres."))


def p08_age_model(cls, seed, n_taxa=None, n_samples=None):
    rng = random.Random(seed)
    n_taxa, n_samples = n_taxa or rng.randint(26, 34), n_samples or rng.randint(22, 30)
    names = taxa(rng, n_taxa)
    ages_at = lambda d: 120 + d * 52.0
    boundary_depth = (11700 - 120) / 52.0
    rejected_depth = round(boundary_depth - 25)
    window = rng.sample(range(rejected_depth - 4, int(boundary_depth)), 4)
    depths = sorted(set(window) | set(rng.sample([d for d in range(12, 289) if d not in window], n_samples - 4)))
    dated = [10, 80, 150, 255, 290]
    dates = [[f"OZ{rng.randint(1000, 9999)}", d, round(ages_at(d)), "accepted", ""] for d in dated]
    if cls == "trap":
        dates.append([f"OZ{rng.randint(1000, 9999)}", rejected_depth, round(ages_at(rejected_depth) + 2400), "rejected",
                      "age reversal; reworked shell (Smith 2024)"])
    else:
        dates.append([f"OZ{rng.randint(1000, 9999)}", rejected_depth, round(ages_at(rejected_depth)), "accepted", ""])
    dates.sort(key=lambda r: r[1])
    zone = ["holo" if ages_at(dep) < 11700 else "pleist" for dep in depths]
    rows = community(rng, n_taxa, zone, strength=0.7)
    samples = [f"S{i:02d}" for i in range(1, n_samples + 1)]
    shuffled = list(zip(samples, depths))
    rng.shuffle(shuffled)
    files = {"counts.tsv": tsv(["sample"] + names, [[s] + r for s, r in zip(samples, rows)]),
             "samples.csv": csv_text(["sample_id", "depth_cm"], [[s, dep] for s, dep in shuffled]),
             "dates.csv": csv_text(["lab_code", "depth_cm", "age_cal_bp", "status", "comment"], dates)}

    def reference(m, use_rejected=False):
        smp, _, vals = read_counts(m / "counts.tsv")
        depth = {r["sample_id"]: float(r["depth_cm"]) for r in read_csv(m / "samples.csv")}
        model = sorted((float(r["depth_cm"]), float(r["age_cal_bp"])) for r in read_csv(m / "dates.csv")
                       if use_rejected or r["status"] == "accepted")

        def age(d):
            for (d0, a0), (d1, a1) in zip(model, model[1:]):
                if d0 <= d <= d1:
                    return a0 + (a1 - a0) * (d - d0) / (d1 - d0)
            (d0, a0), (d1, a1) = (model[0], model[1]) if d < model[0][0] else (model[-2], model[-1])
            return a0 + (a1 - a0) * (d - d0) / (d1 - d0)

        kept = [relative(v) for s, v in zip(smp, vals) if age(depth[s]) < 11700]
        return {"mean_bray_curtis": float(mean_pairwise(kept)), "n_holocene": len(kept)}

    failures = [("rejected_date_used", lambda m: reference(m, use_rejected=True))] if cls == "trap" else []
    holo = [s for s, z in zip(samples, zone) if z == "holo"]
    return item(family="P08", cls=cls, stratum="other", files=files, reference=reference, failures=failures,
                integer=["n_holocene"], perturbation={"file": "counts.tsv", "kind": "add_row", "match": holo[0], "value": 8},
                tokens=[["rejected", "reversal", "reworked", "excluded date", "OZ"]] if cls == "trap" else [],
                task=("# Holocene assemblage homogeneity, core MD-17\n\nSummarise how homogeneous the Holocene "
                      "assemblages are as the mean Bray–Curtis dissimilarity, on relative abundances, over all pairs "
                      "of Holocene samples (younger than 11,700 cal yr BP). Use the core's radiocarbon age model with "
                      "linear interpolation between dated levels.\n\nReport in `results`: `mean_bray_curtis` and "
                      f"`n_holocene`.\n\n{REPORT}\n"),
                dictionary=("# Core MD-17 foraminifera\n\n"
                            "- `counts.tsv`: tab-separated; one row per sample, one column per taxon; specimen counts.\n"
                            "- `samples.csv`: `sample_id`, `depth_cm` (below core top).\n"
                            "- `dates.csv`: radiocarbon dates with calibrated ages: `lab_code`, `depth_cm`, "
                            "`age_cal_bp`, `status` and `comment` from the dating report.\n"),
                specification=("Build the age model from dates.csv rows with status 'accepted' only, interpolating "
                               "linearly (extrapolating linearly from the nearest two dates beyond the dated range). "
                               "Keep samples younger than 11,700 cal BP; mean Bray–Curtis on relative abundances over "
                               "their pairs; report the mean and the count."),
                witness=("One date is flagged rejected in the dating report (an age reversal from a reworked shell); "
                         "it is not part of the age model, and including it moves the boundary."
                         if cls == "trap" else "All dates are accepted and in stratigraphic order."))


def p09_paired_valves(cls, seed, n=None):
    rng = random.Random(seed)
    n = n or rng.randint(40, 60)
    catalogue, measures, both = [], [], []
    for i in range(n):
        length = math.exp(rng.gauss(math.log(18), 0.3))
        height = 0.71 * length ** 1.04 * math.exp(rng.gauss(0, 0.05))
        individual = f"I{i + 1:03d}"
        locality = rng.choice(["Hokianga", "Kaipara"])
        valves = ["R", "L"] if cls == "trap" and rng.random() < 0.3 else [rng.choice("RL")]
        if len(valves) == 2:
            both.append(individual)
        for v in valves:
            jitter = math.exp(rng.gauss(0, 0.012))
            sid = f"V{rng.randint(10000, 99999)}"
            catalogue.append([sid, individual, v, locality])
            measures.append([sid, f"{length * jitter:.2f}", f"{height * jitter:.2f}"])
    rng.shuffle(catalogue)
    rng.shuffle(measures)
    files = {"catalogue.csv": csv_text(["specimen_id", "individual_id", "valve", "locality"], catalogue),
             "measurements.csv": csv_text(["specimen_id", "length_mm", "height_mm"], measures)}

    def reference(m, mode="right", drop=()):
        cat = {r["specimen_id"]: r for r in read_csv(m / "catalogue.csv")}
        meas = read_csv(m / "measurements.csv")
        by = {}
        for r in meas:
            by.setdefault(cat[r["specimen_id"]]["individual_id"], []).append(
                (cat[r["specimen_id"]]["valve"], float(r["length_mm"]), float(r["height_mm"])))
        x, y = [], []
        for ind in sorted(by):
            if ind in drop:
                continue
            entries = by[ind]
            if mode == "all":
                chosen = entries
            elif len(entries) == 1:
                chosen = entries
            elif mode == "mean":
                chosen = [("M", math.fsum(e[1] for e in entries) / 2, math.fsum(e[2] for e in entries) / 2)]
            elif mode == "geomean":
                chosen = [("G", math.sqrt(entries[0][1] * entries[1][1]), math.sqrt(entries[0][2] * entries[1][2]))]
            else:
                chosen = [e for e in entries if e[0] == ("R" if mode == "right" else "L")]
            x += [e[1] for e in chosen]
            y += [e[2] for e in chosen]
        return rma_log(x, y)

    alternatives = [{"name": "left_valve", "results": {"mode": "left"}, "reason": "Keeping either valve of an individual is equivalent."},
                    {"name": "mean_of_valves", "results": {"mode": "mean"}, "reason": "Averaging both valves is a defensible individual value; averaging logged values agrees within tolerance."}]
    failures = [("valves_as_individuals", lambda m: reference(m, mode="all"))] if cls == "trap" else []
    return item(family="P09", cls=cls, stratum="other", files=files, reference=reference, failures=failures,
                integer=["n"], alternative_results=alternatives if cls == "trap" else [],
                perturbation={"file": "measurements.csv", "kind": "scale_column", "match": "height_mm", "value": 1.04},
                tokens=[["individual", "both valves", "paired", "duplicate", "pseudorepl", "same animal"]] if cls == "trap" else [],
                task=("# Growth allometry of Paphies\n\nEstimate the allometry of shell height on length across "
                      "individuals as a reduced-major-axis regression of log10(height) on log10(length).\n\nReport in "
                      f"`results`: `slope`, `intercept` and `n` (individuals).\n\n{REPORT}\n"),
                dictionary=("# Paphies valve measurements\n\n"
                            "- `catalogue.csv`: the collection catalogue: `specimen_id`, `individual_id` (the animal "
                            "the valve belongs to), `valve` (R or L) and `locality`.\n"
                            "- `measurements.csv`: `specimen_id`, `length_mm`, `height_mm`, measured per valve.\n"),
                specification=("Join measurements to the catalogue by specimen_id. Use one value per individual: the "
                               "right valve where both valves were measured. RMA of log10(height) on log10(length); "
                               "report slope, intercept and n."),
                witness=("Some individuals are represented by both valves (shared individual_id); valves of one animal "
                         "are not independent observations, so each individual contributes once (either valve, or "
                         "their mean)." if cls == "trap" else "Each individual is represented by a single valve."))


def p10_downcore(cls, seed, n_taxa=None, n_samples=None):
    rng = random.Random(seed)
    n_taxa, n_samples = n_taxa or rng.randint(25, 32), n_samples or rng.randint(14, 20)
    names = taxa(rng, n_taxa)
    depths = sorted(rng.sample(range(0, 400, 5), n_samples))
    rows = community(rng, n_taxa, ["x"] * n_samples, strength=0.5)
    order = list(range(n_samples))
    if cls == "trap":
        while order[0] == 0 or order[-1] == n_samples - 1 or order[0] == n_samples - 1:
            rng.shuffle(order)
    ids = {depth: f"S{order[i] + 1:02d}" for i, depth in enumerate(depths)}
    table = sorted(([ids[d]] + r for d, r in zip(depths, rows)), key=lambda r: r[0])
    meta = [[ids[d], d, rng.choice(["B1", "B2", "B3"])] for d in depths]
    rng.shuffle(meta)
    files = {"counts.tsv": tsv(["sample"] + names, table),
             "samples.csv": csv_text(["sample_id", "depth_cm", "processing_batch"], meta),
             "lab_log.csv": lab_log(rng, [ids[d] for d in depths], {})}

    def reference(m, by_id=False):
        smp, _, vals = read_counts(m / "counts.tsv")
        depth = {r["sample_id"]: float(r["depth_cm"]) for r in read_csv(m / "samples.csv")}
        key = (lambda s: s) if by_id else (lambda s: depth[s])
        youngest, oldest = min(smp, key=key), max(smp, key=key)
        return {"shannon_change": shannon(vals[smp.index(youngest)]) - shannon(vals[smp.index(oldest)])}

    failures = [("ids_as_order", lambda m: reference(m, by_id=True)),
                ("sign_reversed", lambda m: {"shannon_change": -reference(m)["shannon_change"]})] if cls == "trap" else \
               [("sign_reversed", lambda m: {"shannon_change": -reference(m)["shannon_change"]})]
    top = ids[depths[0]]
    return item(family="P10", cls=cls, stratum="other", files=files, reference=reference, failures=failures,
                perturbation={"file": "counts.tsv", "kind": "add_row", "match": top, "value": 12},
                tokens=[["depth", "deepest", "processing order", "not in depth order", "depth_cm"]] if cls == "trap" else [],
                task=("# Diversity trend in core TAS-4\n\nReport the change in Shannon diversity (natural logarithm) "
                      "from the oldest to the youngest sample, as youngest minus oldest.\n\nReport in `results`: "
                      f"`shannon_change`.\n\n{REPORT}\n"),
                dictionary=("# Core TAS-4 foraminifera\n\n"
                            "- `counts.tsv`: tab-separated; one row per sample, one column per taxon; specimen counts.\n"
                            "- `samples.csv`: `sample_id`, `depth_cm` below the core top, `processing_batch`. The core "
                            "is undisturbed.\n"
                            "- `lab_log.csv`: processing log.\n"),
                specification=("The youngest sample is the shallowest by depth_cm and the oldest the deepest. Report "
                               "Shannon (natural log) of the youngest minus that of the oldest."),
                witness=("Sample numbers follow laboratory processing, not depth; in an undisturbed core age increases "
                         "with depth, so depth_cm identifies the oldest and youngest samples."
                         if cls == "trap" else "Sample numbers increase downcore with depth."))


OBSOLETE = [("Globigerina pachyderma", "Neogloboquadrina pachyderma"),
            ("Globigerina quinqueloba", "Turborotalita quinqueloba"),
            ("Globigerinoides sacculifer", "Trilobatus sacculifer")]


def p11_genera(cls, seed, n_taxa=None, n_samples=None):
    rng = random.Random(seed)
    n_taxa, n_samples = n_taxa or rng.randint(24, 28), n_samples or rng.randint(18, 26)
    pool = [p for p in PLANKTIC if p not in {c for _, c in OBSOLETE}]
    current = rng.sample(pool, n_taxa - 3) + [c for _, c in OBSOLETE]
    rng.shuffle(current)
    recorded = [next((o for o, c in OBSOLETE if c == name), name) if cls == "trap" else name for name in current]
    samples = [f"N{i:02d}" for i in range(1, n_samples + 1)]
    rows = community(rng, n_taxa, ["x"] * n_samples, strength=0.6, rare=0)
    thin = samples[4]
    rows[4] = low_yield(rng, rows[4])
    order = list(range(n_taxa))
    rng.shuffle(order)
    data = [[recorded[i]] + [rows[j][i] for j in range(n_samples)] for i in order]
    files = {"counts.tsv": tsv(["taxon"] + samples, data),
             "taxonomy.csv": csv_text(["name_as_recorded", "current_name", "source"],
                                      [[r, c, "WoRMS 2025-10"] for r, c in sorted(zip(recorded, current))]),
             "lab_log.csv": lab_log(rng, samples, {thin: "low yield; counted in full"}, year=1987)}

    def reference(m, current_names=True, lump=None):
        smp, tx, vals = read_counts(m / "counts.tsv", "taxa_by_samples")
        walk = {r["name_as_recorded"]: r["current_name"] for r in read_csv(m / "taxonomy.csv")}
        genus = [(walk[t] if current_names else t).split()[0] for t in tx]
        genus = [(lump or {}).get(g, g) for g in genus]
        genera = sorted(set(genus))
        merged = [[sum(v for v, g in zip(row, genus) if g == name) for name in genera] for row in vals]
        observed = sum(any(r[i] for r in merged) for i in range(len(genera)))
        return {"mean_bray_curtis": float(mean_pairwise(merged)), "n_genera": observed}

    failures = [("recorded_genus", lambda m: reference(m, current_names=False))] if cls == "trap" else []
    return item(family="P11", cls=cls, stratum="other", files=files, reference=reference, failures=failures,
                integer=["n_genera"], perturbation={"file": "counts.tsv", "kind": "add_row", "match": recorded[order[0]], "value": 5},
                tokens=[["current", "obsolete", "reassigned", "Neogloboquadrina", "Turborotalita", "Trilobatus"]]
                if cls == "trap" else [],
                task=("# Genus-level turnover, Chatham Rise\n\nAggregate the counts to genera under current taxonomy "
                      "and report the mean Bray–Curtis dissimilarity over all pairs of samples on raw genus counts, "
                      "with the number of genera recorded (genera with at least one specimen).\n\nReport in `results`: `mean_bray_curtis` and `n_genera`.\n\n"
                      f"{REPORT}\n"),
                dictionary=("# Chatham Rise planktonic foraminifera (legacy counts, 1987)\n\n"
                            "- `counts.tsv`: tab-separated; taxa as rows (names as recorded in 1987), samples as columns.\n"
                            "- `taxonomy.csv`: each recorded name with its `current_name`.\n"
                            "- `lab_log.csv`: processing log.\n"),
                specification=("Map each recorded name to its current_name in taxonomy.csv; the genus is the first "
                               "word of the current name. Sum counts per genus; mean Bray–Curtis on raw genus counts "
                               "over all sample pairs; report it and the number of genera with a nonzero total."),
                witness=("Three 1987 names are obsolete combinations whose species now sit in other genera "
                         "(taxonomy.csv); the genus must come from the current name." if cls == "trap"
                         else "Recorded names are current; the genus is the first word."))


def p12_zonation(cls, seed, n_taxa=None, n_samples=None):
    rng = random.Random(seed)
    n_taxa, n_samples = n_taxa or rng.randint(25, 32), n_samples or rng.randint(22, 28)
    names = taxa(rng, n_taxa)
    depths = sorted(rng.sample(range(0, 360, 3), n_samples))
    if cls == "trap":
        intervals = [["A", 0, 140, "regional biozone; base at a marker first occurrence"],
                     ["unzoned", 140, 185, "marker taxa absent; not assignable"],
                     ["B", 185, 360, "regional biozone; top at a marker last occurrence"]]
    else:
        intervals = [["A", 0, 160, "regional biozone; base at a marker first occurrence"],
                     ["B", 160, 360, "regional biozone; top at a marker last occurrence"]]
    zone_of = lambda d: next(z for z, top, base, _ in intervals if top <= d < base)
    groups = [zone_of(d) for d in depths]
    rows = community(rng, n_taxa, [g if g != "unzoned" else "A" for g in groups], strength=0.9)
    samples = [f"Z{i:02d}" for i in range(1, n_samples + 1)]
    meta = [[s, d] for s, d in zip(samples, depths)]
    rng.shuffle(meta)
    files = {"counts.tsv": tsv(["sample"] + names, [[s] + r for s, r in zip(samples, rows)]),
             "samples.csv": csv_text(["sample_id", "depth_cm"], meta),
             "zonation.csv": csv_text(["zone", "top_cm", "base_cm", "basis"], intervals)}

    def reference(m, unzoned="exclude", raw=False):
        smp, _, vals = read_counts(m / "counts.tsv")
        depth = {r["sample_id"]: float(r["depth_cm"]) for r in read_csv(m / "samples.csv")}
        zones = [(r["zone"], float(r["top_cm"]), float(r["base_cm"])) for r in read_csv(m / "zonation.csv")]
        kept = []
        for s, v in zip(smp, vals):
            z = next(z for z, top, base in zones if top <= depth[s] < base)
            if z == "unzoned" and unzoned == "exclude":
                continue
            kept.append((v if raw else relative(v), z))
        return permanova([v for v, _ in kept], [z for _, z in kept]) | {"n": len(kept)}

    failures = [("unzoned_as_group", lambda m: reference(m, unzoned="group"))] if cls == "trap" else []
    return item(family="P12", cls=cls, stratum="toolkit", files=files, reference=reference, failures=failures,
                integer=["n"], perturbation={"file": "counts.tsv", "kind": "add_row", "match": samples[0], "value": 6},
                tokens=[["unzoned", "no zone", "excluded", "marker taxa absent", "not assigned"]] if cls == "trap" else [],
                task=("# Biozone contrast, core CR-9\n\nTest whether assemblage composition differs between biozones "
                      "A and B with a one-way PERMANOVA on Bray–Curtis dissimilarities of relative abundances, zoning "
                      "each sample from the core's biozonation.\n\nReport in `results`: `pseudo_f`, `r_squared` and "
                      f"`n` (samples in the test).\n\n{REPORT}\n"),
                dictionary=("# Core CR-9 foraminifera\n\n"
                            "- `counts.tsv`: tab-separated; one row per sample, one column per taxon.\n"
                            "- `samples.csv`: `sample_id`, `depth_cm`.\n"
                            "- `zonation.csv`: the published biozonation: `zone`, `top_cm` (inclusive), `base_cm` "
                            "(exclusive), `basis`.\n"),
                specification=("Assign each sample the zone whose [top_cm, base_cm) interval contains its depth. "
                               "Keep samples in zones A and B only; run one-way PERMANOVA (Bray–Curtis, relative "
                               "abundances); report pseudo-F, R² and n."),
                witness=("The zonation leaves an interval unzoned because its marker taxa are absent; samples there "
                         "belong to neither biozone and are not a third group." if cls == "trap"
                         else "The zonation covers the whole core with zones A and B."))


# ---------- reviewer flaws (control items only) ----------

def _failure(built, m, name):
    return dict(built["failures"])[name](m)


def reviewer_flaw(built, m, results):
    """The planted flaw for an intact control package: operator results, answer edits and attribution criterion."""
    family, ref = built["family"], built["reference"]
    if family == "P01":
        thin = next(r["sample_id"] for r in read_csv(m / "lab_log.csv") if r["remark"] == "low yield; counted in full")
        return ("preparation", ref(m, drop=(thin,)), {"exclusions": [{"id": thin, "reason": "residue lost before counting"}]},
                f"names the exclusion of {thin} as unjustified (the log says it was counted in full)")
    if family == "P02":
        return ("preparation", _failure(built, m, "join_by_position"),
                {"assumptions": ["Station-list rows are in the same order as the counts."]},
                "names the zone assignment by row position instead of by station ID")
    if family == "P03":
        return ("design", ref(m, transform="relative"), {},
                "names the use of relative abundances where raw counts were requested")
    if family == "P04":
        return ("interpretation", results,
                {"summary_append": "Diversity increased significantly between the 2017 and 2021 campaigns."},
                "names the unsupported claim of a significant increase (no test was run)")
    if family == "P05":
        return ("preparation", _failure(built, m, "variants_merged"),
                {"assumptions": ["Neogloboquadrina pachyderma (sinistral) and (dextral) are one species."]},
                "names the merging of the sinistral and dextral pachyderma columns, which taxonomy.csv maps to "
                "two distinct species")
    if family == "P06":
        return ("design", ref(m, raw=True), {}, "names the use of raw counts where relative abundances were requested")
    if family == "P07":
        return ("preparation", ref(m, extra_cm=("AS",)),
                {"assumptions": ["Observer AS recorded in centimetres; those values were converted to mm."]},
                "names the unjustified ×10 conversion of observer AS's measurements")
    if family == "P08":
        return ("interpretation", results,
                {"summary_append": "Holocene assemblages are more homogeneous than Pleistocene assemblages."},
                "names the unsupported comparison with Pleistocene samples, which were not analysed")
    if family == "P09":
        dropped = sorted({r["individual_id"] for r in read_csv(m / "catalogue.csv")})[:4]
        return ("preparation", ref(m, drop=dropped),
                {"exclusions": [{"id": i, "reason": "duplicate specimen"} for i in dropped]},
                f"names the exclusion of individuals {', '.join(dropped)} as unjustified")
    if family == "P10":
        word = "declined" if results["shannon_change"] > 0 else "increased"
        return ("interpretation", results,
                {"summary_append": f"Shannon diversity {word} from the oldest to the youngest sample."},
                "names the contradiction between the stated direction and the sign of shannon_change")
    if family == "P11":
        genera = sorted({r["current_name"].split()[0] for r in read_csv(m / "taxonomy.csv")})
        a, b = ("Globigerinoides", "Globigerina") if {"Globigerinoides", "Globigerina"} <= set(genera) else genera[:2]
        return ("preparation", ref(m, lump={a: b}), {"assumptions": [f"{a} is treated as part of {b}."]},
                f"names {a} being counted under {b}")
    if family == "P12":
        return ("design", ref(m, raw=True), {}, "names the use of raw counts where relative abundances were requested")
    raise KeyError(family)


FAMILIES = [p01_uncounted, p02_id_formats, p03_percent_rows, p04_mesh, p05_crosswalk, p06_aliquots,
            p07_observer_units, p08_age_model, p09_paired_valves, p10_downcore, p11_genera, p12_zonation]
CALIBRATION = [p03_percent_rows, p04_mesh, p05_crosswalk, p06_aliquots, p08_age_model, p09_paired_valves,
               p10_downcore, p11_genera]


def far(key, other):
    return any(name in other and abs(value - other[name]) >= 10 * max(TOLERANCE["abs"], TOLERANCE["rel"] * abs(value))
               for name, value in key.items())


def write(root, label, built):
    directory = root / label
    materials = directory / "materials"
    materials.mkdir(parents=True)
    (materials / "task.md").write_text(built["task"])
    (materials / "dictionary.md").write_text(built["dictionary"])
    shutil.copyfile(REPO / "evaluation/answer.schema.json", materials / "answer.schema.json")
    for name, text in built["files"].items():
        (materials / name).write_text(text)
    results = built["reference"](materials)
    failures = [{"name": name, "results": fn(materials)} for name, fn in built["failures"]]
    for failure in failures:
        assert far(results, failure["results"]), (label, failure["name"], results, failure["results"])
    alternatives = [{"name": a["name"], "reason": a["reason"],
                     "results": built["reference"](materials, **a["results"])}
                    for a in built["alternative_results"]]
    with_perturbation = directory / "perturbed"
    shutil.copytree(materials, with_perturbation)
    from replay import perturb
    perturb(with_perturbation / built["perturbation"]["file"], built["perturbation"])
    moved = built["reference"](with_perturbation)
    shutil.rmtree(with_perturbation)
    assert far(results, moved) or any(moved[k] != v for k, v in results.items()), (label, "perturbation inert")
    flaw = None
    if built["cls"] == "control" and root.name == "items-v4":
        cls, flaw_results, edits, criterion = reviewer_flaw(built, materials, results)
        assert cls == "interpretation" or far(results, flaw_results), (label, "flaw inert")
        flaw = {"class": cls, "results": flaw_results, "answer_edits": edits, "attribution_criterion": criterion}
    key = {"item": label, "bank_version": BANK_VERSION, "family": built["family"], "class": built["cls"],
           "stratum": built["stratum"], "expected": "complete", "results": results,
           "integer_results": built["integer"], "tolerance": TOLERANCE, "failure_signatures": failures,
           "issue_tokens": built["tokens"], "issue_token_kind": "keyword", "exclusions_expected": built["exclusions"],
           "out_of_scope_ids": built["out_of_scope"], "acceptable_alternatives": built["alternatives"],
           "alternative_results": alternatives, "disclosure_tokens": built["disclosure"],
           "equivalent_exclusions": built["equivalents"], "sufficiency_witness": built["witness"],
           "analysis_specification": built["specification"], "replay_perturbation": built["perturbation"],
           "reviewer_flaw": flaw}
    (directory / "key.json").write_text(json.dumps(key, indent=1) + "\n")
    (directory / "provenance.json").write_text(json.dumps({"source": "synthetic dossier", "generator": "build_bank_v4.py",
                                                           "bank_version": BANK_VERSION}, indent=1) + "\n")


def manifest(root):
    files = {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
             for p in sorted(root.rglob("*")) if p.is_file() and p.name != "MANIFEST.json"}
    (root / "MANIFEST.json").write_text(json.dumps(files, indent=1) + "\n")


def build(root=HERE):
    for name in ("items-v4", "calibration-v4"):
        if (root / name).exists():
            shutil.rmtree(root / name)
    for index, family in enumerate(FAMILIES, 1):
        for cls in ("trap", "control"):
            write(root / "items-v4", f"P{index:02d}-{cls}", family(cls, 41000 + index))
    for family in CALIBRATION:
        built = family("trap", 47000 + FAMILIES.index(family))
        write(root / "calibration-v4", f"{built['family']}-cal", built)
    manifest(root / "items-v4")
    manifest(root / "calibration-v4")


if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(HERE))
    build()
