"""Frozen intake and design for the Lake Selina application (stage 1). Run: uv run analyses/lake-selina/intake.py

Reads the saved Neotoma responses, writes the count table, the level annotations and design.json.
It computes no composition, richness or test result. Extraction from JSON, ecological-group
filtering and endpoint selection from archived ages are unsupported intake steps (declared in
INTAKE.md); count totals, resource bounds and the declared pairs are checked by toolkit validation.
"""

import hashlib
import json
from pathlib import Path

import palaeo_agent as pa

HERE = Path(__file__).resolve().parent
SOURCE = HERE / "source/neotoma-52767-download.json"
CHRONOLOGIES = HERE / "source/neotoma-52767-chronologies.json"
SOURCE_SHA256 = "5dd1a71cf7a655f08441e59b866b3eb64c893b164cc8e9320d9ea2d7507ead24"
CHRONOLOGIES_SHA256 = "8bda8c89b64fab4def996b43cbe3e2b431a1ff374f9a863f1d127878b7764f61"
PRIMARY, ALTERNATIVE = 37590, 37589
SUM_GROUPS = ("TRSH", "UPHE")
WINDOWS = {
    "historical_45_38ka": (38000, 45000),
    "benchmark_mis3_lgm": (21000, 28000),
    "benchmark_lateglacial_holocene": (8000, 15000),
}
SIMULATIONS, SEED, SIZE = 99999, 7112026, 282


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def bracket(levels, key, window):
    young, old = window
    above = [lv for lv in levels if lv[key] <= young]
    below = [lv for lv in levels if lv[key] >= old]
    if not above or not below:
        return None
    return max(above, key=lambda lv: lv[key]), min(below, key=lambda lv: lv[key])


def main():
    for path, expected in ((SOURCE, SOURCE_SHA256), (CHRONOLOGIES, CHRONOLOGIES_SHA256)):
        if sha(path) != expected:
            raise SystemExit(f"{path.name} differs from the frozen source")
    dataset = json.loads(SOURCE.read_text())["data"][0]["site"]["collectionunit"]["dataset"]
    samples = sorted(dataset["samples"], key=lambda s: s["depth"])
    taxa, counts, levels = {}, [], []
    for s in samples:
        row = {}
        for d in s["datum"]:
            if d["element"] != "pollen" or d["ecologicalgroup"] not in SUM_GROUPS:
                continue
            if d["units"] != "NISP" or type(d["value"]) is not int or d["value"] <= 0:
                raise SystemExit("expected positive integer NISP entries (the archive stores no zeros)")
            if d["variablename"] in row or taxa.get(d["variablename"], d["taxonid"]) != d["taxonid"]:
                raise SystemExit(f"taxon label not unique: {d['variablename']}")
            taxa[d["variablename"]] = d["taxonid"]
            row[d["variablename"]] = d["value"]
        counts.append(row)
        ages = {a["chronologyid"]: a for a in s["ages"]}
        levels.append({"sample_id": str(s["sampleid"]), "depth_cm": s["depth"],
                       "age_ippd2": ages[PRIMARY]["age"], "age_ippd2_younger": ages[PRIMARY]["ageyounger"],
                       "age_ippd2_older": ages[PRIMARY]["ageolder"], "age_ippd1": ages[ALTERNATIVE]["age"]})
    names = sorted(taxa)
    lines = ["\t".join(["sample_id", *names])]
    lines += ["\t".join([lv["sample_id"], *[str(row.get(n, 0)) for n in names]]) for lv, row in zip(levels, counts)]
    table = HERE / "data/counts.tsv"
    table.parent.mkdir(exist_ok=True)
    table.write_text("\n".join(lines) + "\n")
    cols = list(levels[0])
    (HERE / "data/levels.csv").write_text("\n".join([",".join(cols)] + [",".join(str(lv[c]) for c in cols)
                                                                        for lv in levels]) + "\n")
    (HERE / "data/taxa.csv").write_text("label,neotoma_taxonid\n" + "".join(f"{n},{taxa[n]}\n" for n in names))

    named, sensitivity = {}, {}
    for name, window in WINDOWS.items():
        primary = bracket(levels, "age_ippd2", window)
        alternative = bracket(levels, "age_ippd1", window)
        named[name] = {"window_cal_bp": list(window),
                       "rule": "young endpoint: deepest-age level with IPPD-2 point age <= window young bound; "
                               "old endpoint: level with smallest IPPD-2 point age >= window old bound",
                       "endpoints": [{k: lv[k] for k in cols} for lv in primary],
                       "elapsed_ippd2_years": primary[1]["age_ippd2"] - primary[0]["age_ippd2"]}
        named[name]["levels_between"] = sum(primary[0]["depth_cm"] < lv["depth_cm"] < primary[1]["depth_cm"]
                                            for lv in levels)
        same = alternative is not None and [lv["sample_id"] for lv in alternative] == \
            [lv["sample_id"] for lv in primary]
        sensitivity[name] = {"ippd1_selects_same_endpoints": same,
                             "ippd1_endpoints": None if alternative is None else
                             [{k: lv[k] for k in cols} for lv in alternative]}

    ids = [lv["sample_id"] for lv in levels]
    pairs = [[a, b] for a, b in zip(ids, ids[1:])]
    extra = [[e["sample_id"] for e in v["endpoints"]] for v in named.values()]
    extra += [[e["sample_id"] for e in v["ippd1_endpoints"]] for v in sensitivity.values()
              if v["ippd1_endpoints"] and not v["ippd1_selects_same_endpoints"]]
    for p in extra:
        if p not in pairs:
            pairs.append(p)

    base = {"input": "data/counts.tsv", "format": "delimited", "delimiter": "tab", "orientation": "samples_by_taxa",
            "value_type": "count", "missing": "error", "empty_samples": "error"}
    specs = {
        "rarefaction": dict(base, method="rarefaction", sizes=[SIZE]),
        "count_homogeneity": dict(base, method="count_homogeneity", pairs=pairs, simulations=SIMULATIONS, seed=SEED),
        "community_relative_braycurtis": dict(base, method="community", distance="braycurtis",
                                              transform="relative_abundance", dimensions=3),
        "community_raw_braycurtis": dict(base, method="community", distance="braycurtis", transform="none",
                                         dimensions=3),
        "community_jaccard": dict(base, method="community", distance="jaccard", transform="none",
                                  dimensions=3),
    }
    data = table.read_bytes()
    validation = {
        "rarefaction": pa.validate_rarefaction(pa.RarefactionSpec(**specs["rarefaction"]), data),
        "community": [pa.CommunitySpec(**specs[k]).method for k in specs if k.startswith("community")],
        "count_homogeneity": pa.validate_count_homogeneity(pa.CountHomogeneitySpec(**specs["count_homogeneity"]),
                                                           data),
    }
    design = {
        "stage": "1: intake and design, frozen before any composition result was computed or viewed",
        "source": {"neotoma_dataset": 52767, "collection": "SEL1999", "sha256": SOURCE_SHA256,
                   "chronologies_sha256": CHRONOLOGIES_SHA256, "dois": dataset["doi"],
                   "publication_doi": "10.1016/S1040-6182(98)00046-9", "license": "CC BY 4.0 (Neotoma policy)"},
        "pollen_sum": {"rule": "element pollen; ecological group TRSH or UPHE; NISP; source labels kept; "
                               "no aggregation; absent entry = zero count (archive stores no zero entries)",
                       "n_levels": len(levels), "n_taxa": len(names),
                       "excluded_categories": "spores (VACR, AQBR, AQVP) and aquatic pollen (AQVP)"},
        "chronology": {"primary": "IPPD-2 (37590, Bacon); ages are annotations only",
                       "alternative": "IPPD-1 (37589, best-fit curve), used only to check endpoint selection"},
        "named_comparisons": named, "chronology_sensitivity": sensitivity,
        "declared_pairs": {"n": len(pairs), "adjacent": len(ids) - 1, "named_or_sensitivity": len(pairs) - len(ids) + 1,
                           "pairs": pairs},
        "specs": specs, "validation": validation,
        "intake_script_sha256": sha(Path(__file__)), "counts_sha256": hashlib.sha256(data).hexdigest(),
    }
    (HERE / "design.json").write_text(json.dumps(design, indent=1) + "\n")
    print(json.dumps({k: design[k] for k in ("named_comparisons", "chronology_sensitivity")}, indent=1))
    print(json.dumps({"pairs": design["declared_pairs"]["n"], "validation": {k: v["status"] for k, v in validation.items() if isinstance(v, dict)}}))


if __name__ == "__main__":
    main()
