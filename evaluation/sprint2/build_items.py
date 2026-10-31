"""Build six development items from exact definitions, without the toolkit."""

import hashlib
import itertools
import json
from fractions import Fraction
from pathlib import Path

HERE = Path(__file__).resolve().parent
VERSION = "sprint2-group-bank-v1"
TOLERANCE = {"abs": 1e-4, "rel": 1e-4}


def digest(data):
    return hashlib.sha256(data).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def as_floats(value):
    if isinstance(value, dict):
        return {k: as_floats(v) for k, v in value.items()}
    return float(value) if isinstance(value, Fraction) else value


def as_rationals(value):
    if isinstance(value, dict):
        return {k: as_rationals(v) for k, v in value.items()}
    return str(value) if isinstance(value, Fraction) else value


def reference(xs, labels):
    """Rows [x, 100-x] have Bray-Curtis distance abs(x-y)/100."""
    n = len(xs)
    names = sorted(set(labels))
    assert len(names) == 2
    q = [[Fraction((a - b) ** 2, 10_000) for b in xs] for a in xs]
    total = sum(q[i][j] for i in range(n) for j in range(i + 1, n)) / n

    def parts(first):
        first = set(first)
        groups = [first, set(range(n)) - first]
        within = sum(sum(q[i][j] for i in group for j in group if i < j) / len(group)
                     for group in groups)
        between = total - within
        return within, between, between / (within / (n - 2)) if within else None

    selected = [i for i, group in enumerate(labels) if group == names[0]]
    within, between, observed = parts(selected)
    assert observed is not None and total > 0 and within > 0
    allocations = list(itertools.combinations(range(n), len(selected)))
    statistics = [parts(group)[2] for group in allocations]
    exceedances = sum(value is None or value >= observed for value in statistics)
    means = {}
    for name in names:
        values = [Fraction(x, 100) for x, label in zip(xs, labels, strict=True) if label == name]
        centroid = sum(values) / len(values)
        means[name] = sum(abs(value - centroid) for value in values) / len(values)
    return {
        "n": n, "pseudo_f": observed, "r_squared": between / total,
        "p_value": Fraction(exceedances, len(allocations)), "ss_total": total,
        "ss_within": within, "ss_between": between, "df_between": 1, "df_within": n - 2,
        "group_mean_centroid_distance": means,
    }, {"mode": "exact", "allocations": len(allocations), "exceedances": exceedances,
        "observed_allocation_included_once": True, "group_order": names}


TASK = """# Community group comparison

Assess the facies-associated difference in community composition using a one-way
PERMANOVA with Bray-Curtis dissimilarity on the untransformed specimen counts.
Use freely exchangeable independent sampling units only when the sampling
description supports that design. Do not aggregate samples or substitute a
different experimental design. Use seed 20261031 and 999 requested permutations;
enumerate all distinct allocations preserving group sizes when feasible.

Report these numerical fields in `results`: `n`, `pseudo_f`, `r_squared`,
`p_value`, `ss_total`, `ss_within`, `ss_between`, `df_between`, `df_within`, and
`group_mean_centroid_distance` (an object with `reef` and `lagoon` means).
The centroid distances are descriptive, without bias adjustment or distance
correction; no dispersion significance test is requested.

Use `answer.json` with the supplied answer contract. Explain the design
assumptions, limitations and handling of identified data problems. If the
requested design is unsupported, set `status` to `stopped`, leave `results`
empty, and identify the sampling units and unsupported design in `issues`.
Preserve your analysis code or specification and enough provenance to rerun it.
Do not launch other agents, agent CLIs or child agent sessions.
"""


def dictionary(ids, dependent=False):
    design = ("Four subsamples were taken within each of two sites. Rows S1-S4 are subsamples of "
              "site_reef_01, and rows S5-S8 are subsamples of site_lagoon_01. Facies is a site-level "
              "attribute. Subsamples within a site share the same exposure and are not independent "
              "replicates of the facies comparison. There is one site per facies."
              if dependent else
              "Each row is one distinct site sampled once. The sites are independent sampling units, "
              "and facies labels are assumed freely exchangeable under the null. There are no "
              "blocks, covariates, repeated measurements or nested subsamples.")
    return ("# Data dictionary\n\n`counts.tsv` is tab-separated in PAST-style tabular format: "
            "the top-left cell is `.`, the first row names the taxa, and the first column contains "
            "sample IDs. Samples are rows; taxa are columns. Values are nonnegative integer "
            "specimen counts, not percentages. There are no missing values or empty samples. "
            "Use no transformation or normalisation.\n\n`samples.csv` is comma-separated, one row "
            "per sample with `sample_id`, `facies` and `site_id`. `sample_id` identifies count-table "
            "rows and metadata records.\n\nCount-table sample order: " + ", ".join(ids) + ".\n\n"
            + design + "\n")


def build_bank():
    bank = {}
    for family in ("G1", "G2", "G3"):
        for variant in ("trap", "twin"):
            item_id = f"{family}-{variant}"
            xs = ([80, 81, 82, 83, 10, 20, 30, 40, 50, 90] if variant == "trap"
                  else [80, 82, 84, 86, 14, 16, 18, 20, 22, 24]) if family == "G3" else [
                      90, 88, 86, 84, 20, 18, 16, 14]
            ids = [f"S{i + 1}" for i in range(len(xs))]
            labels = ["reef"] * 4 + ["lagoon"] * (len(xs) - 4)
            dependent = family == "G2" and variant == "trap"
            order = [4, 0, 5, 1, 6, 2, 7, 3] if family == "G1" and variant == "trap" else list(range(len(xs)))
            site_ids = (["site_reef_01"] * 4 + ["site_lagoon_01"] * 4 if dependent
                        else [f"site_{i + 1:02d}" for i in range(len(xs))])
            files = {
                "counts.tsv": ".\tDalmanella\tSowerbyella\n" + "".join(
                    f"{sample}\t{x}\t{100 - x}\n" for sample, x in zip(ids, xs, strict=True)),
                "samples.csv": "sample_id,facies,site_id\n" + "".join(
                    f"{ids[i]},{labels[i]},{site_ids[i]}\n" for i in order),
                "dictionary.md": dictionary(ids, dependent), "task.md": TASK,
            }
            results, exact = reference(xs, labels)
            signatures = []
            issue_tokens = []
            purpose = ""
            if family == "G1":
                purpose = "Exact sample-ID metadata alignment; differently ordered metadata is the trap."
                if variant == "trap":
                    wrong, _ = reference(xs, [labels[i] for i in order])
                    signatures.append({"name": "positional_join", "results": as_floats(wrong)})
                    issue_tokens = [["align", "join", "sample id", "order"]]
            elif family == "G2":
                purpose = "Dependent within-site subsamples must stop; the clean twin has independent sites."
                if dependent:
                    signatures.append({"name": "subsamples_as_independent", "results": as_floats(results)})
                    issue_tokens = [["site_reef_01"], ["site_lagoon_01"],
                                    ["depend", "pseudorep", "subsample", "replicat"]]
            else:
                purpose = ("Response to a supplied interpretation claim, with numerical and descriptive "
                           "centroid diagnostics; not an independent-interpretation efficacy test.")
                claim = ("The facies differ in centroid location, and differences in within-facies spread "
                         "cannot explain the significant PERMANOVA result." if variant == "trap" else
                         "The data show a facies-associated community difference under the stated "
                         "exchangeability assumption. Distances to group centroids describe within-facies "
                         "spread separately; they do not isolate a pure location effect.")
                files["task.md"] += ("\nA draft interpretation says: \"" + claim + "\"\n\n"
                    "Assess that exact claim. Also report `claim_supported` as 1 if the evidence "
                    "supports the full claim, otherwise 0, and explain your judgment in `summary`.\n")
                results["claim_supported"] = 0 if variant == "trap" else 1
                if variant == "trap":
                    wrong = as_floats(results) | {"claim_supported": 1}
                    signatures.append({"name": "dispersion_as_pure_location", "results": wrong})
                    issue_tokens = [["dispers", "spread", "location", "centroid"]]
            key = {
                "item": item_id, "catalogue": family, "class": variant,
                "expected": "unresolved" if dependent else "complete",
                "results": {} if dependent else as_floats(results),
                "integer_results": ["n", "df_between", "df_within"] + (["claim_supported"] if family == "G3" else []),
                "tolerance": TOLERANCE, "failure_signatures": signatures,
                "issue_tokens": issue_tokens, "issue_token_kind": "keyword" if issue_tokens else None,
                "exclusions_expected": [], "smoke": True,
                "requires_stopped_empty_results": dependent,
            }
            assignments = list(zip(ids, labels, strict=True))
            provenance = {
                "item": item_id, "version": VERSION, "purpose": purpose,
                "generator": "evaluation/sprint2/build_items.py", "generator_sha256": digest(Path(__file__).read_bytes()),
                "data": "Synthetic declared integer counts; each row totals 100.",
                "key_method": "Standalone Python stdlib Fraction arithmetic, all distinct group allocations, and one-dimensional centroid geometry; no palaeo_agent imports.",
                "rational_results": None if dependent else as_rationals(results), "enumeration": None if dependent else exact,
                "group_assignments_sha256": digest(canonical(assignments)),
                "group_assignments": assignments,
                "sampling_units_sha256": digest(canonical(list(zip(ids, site_ids, strict=True)))),
                "materials_sha256": {name: digest(value.encode()) for name, value in sorted(files.items())},
            }
            bank[item_id] = {"files": files, "key": key, "provenance": provenance}
    return bank


def write_bank(root):
    root = Path(root)
    bank = build_bank()
    for item_id, item in bank.items():
        dest = root / item_id
        (dest / "materials").mkdir(parents=True, exist_ok=True)
        for name, text in item["files"].items():
            (dest / "materials" / name).write_text(text)
        for name in ("key", "provenance"):
            (dest / f"{name}.json").write_text(json.dumps(item[name], indent=2) + "\n")
    manifest = {"version": VERSION, "items": sorted(bank), "files": {
        str(path.relative_to(root)): digest(path.read_bytes())
        for path in sorted(root.rglob("*")) if path.is_file() and path.name != "MANIFEST.json"}}
    (root / "MANIFEST.json").write_text(json.dumps(manifest, indent=2) + "\n")
    return manifest


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path, nargs="?", default=HERE / "items")
    args = parser.parse_args()
    print(json.dumps(write_bank(args.root), indent=2))
