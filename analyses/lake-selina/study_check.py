"""Sprint 9 dogfood: rebuild amendment 1 as one toolkit study and compare with results-amended.json.

Run: uv run analyses/lake-selina/study_check.py. The study starts from the archived 66-category table,
removes the six sedge and aquatic columns with the study operation exclude_taxa, and runs
count_homogeneity with pairs "adjacent" plus the six amendment-1 extras, rarefaction at minimum_total and
the three community runs. No bespoke table editing, pair listing or Holm postprocessing. Writes
study-check.json; the study bundle goes to runs-study/ (gitignored).
"""

import json
import shutil
from pathlib import Path

import palaeo_agent as pa
from amend_source import EXCLUDED

HERE = Path(__file__).resolve().parent
COMMON = {"format": "past", "orientation": "samples_by_taxa", "value_type": "count", "missing": "error",
          "empty_samples": "error"}


def main():
    design = json.loads((HERE / "design-amended.json").read_text())
    extras = design["specs"]["count_homogeneity"]["pairs"][design["declared_pairs"]["adjacent"]:]
    study = {
        "study_version": 1,
        "inputs": {"archive": {"kind": "counts", "path": "data/counts.tsv", "format": "delimited",
                               "delimiter": "tab", "orientation": "samples_by_taxa"}},
        "datasets": {"dryland": {"source": "archive", "operations": [
            {"op": "exclude_taxa", "taxa": [t for group in EXCLUDED.values() for t in group],
             "reason": "dryland pollen sum, Colhoun et al. (1999): sedges and aquatics excluded"}]}},
        "analyses": [
            {"id": "rarefaction", "dataset": "dryland", "spec": dict(COMMON, method="rarefaction", sizes="minimum_total")},
            {"id": "count_homogeneity", "dataset": "dryland",
             "spec": dict(COMMON, method="count_homogeneity", pairs="adjacent", extra_pairs=extras,
                          simulations=99999, seed=7112026)},
            *[{"id": name, "dataset": "dryland",
               "spec": dict(COMMON, method="community", distance=d, transform=tr, dimensions=3)}
              for name, d, tr in (("community_relative_braycurtis", "braycurtis", "relative_abundance"),
                                  ("community_raw_braycurtis", "braycurtis", "none"),
                                  ("community_jaccard", "jaccard", "none"))]],
    }
    (HERE / "study-dryland.json").write_text(json.dumps(study, indent=1) + "\n")
    out = HERE / "runs-study"
    shutil.rmtree(out, ignore_errors=True)
    outcome = pa.run_study(HERE / "study-dryland.json", out)
    assert outcome["status"] == "complete", outcome
    inspected = pa.inspect_study(outcome["study_dir"])
    directory = Path(outcome["study_dir"])
    runs = {k: json.loads((directory / v["run_dir"] / "results.json").read_text())
            for k, v in json.loads((directory / "manifest.json").read_text())["runs"].items()}

    derived = (directory / "derived/dryland.dat").read_text().splitlines()
    manual = (HERE / "data/counts-dryland.tsv").read_text().splitlines()
    table_identical = [line.split("\t")[1:] for line in derived] == [line.split("\t")[1:] for line in manual]

    old = json.loads((HERE / "results-amended.json").read_text())
    old_pairs = old["adjacent_steps"] + [v[k] for v in old["named_comparisons"].values()
                                         for k in ("primary", "ippd1_sensitivity")]
    old_by = {(s["younger"], s["older"]): s for s in old_pairs}
    hom = runs["count_homogeneity"]
    diffs = {"p_value": 0.0, "p_value_holm": 0.0, "holm_envelope": 0.0}
    flags_agree, compared = True, 0
    for pair in hom["pairs"]:
        s = old_by.get(tuple(pair["sample_ids"]))
        if s is None:
            continue
        compared += 1
        diffs["p_value"] = max(diffs["p_value"], abs(pair["p_value"] - s["p_value"]))
        diffs["p_value_holm"] = max(diffs["p_value_holm"], abs(pair["p_value_holm"] - s["p_value_holm"]))
        diffs["holm_envelope"] = max(diffs["holm_envelope"], *(abs(a - b) for a, b in
                                                               zip(pair["monte_carlo"]["holm_envelope"], s["holm_envelope"])))
        flags_agree &= pair["monte_carlo"]["holm_envelope_unresolved"] == s["monte_carlo_sensitive"]
    rare = {s["sample_id"]: s["estimates"][0] for s in runs["rarefaction"]["samples"]}
    richness_diff = max(abs(rare[lv["sample_id"]]["expected_richness"] - lv["expected_richness_272"]) for lv in old["levels"])
    check = {
        "study_status": inspected["status"],
        "derived_table_identical_to_amend_source_output": table_identical,
        "pair_declaration": hom["pair_declaration"],
        "resolved_pairs_identical_to_amendment_1": [p["sample_ids"] for p in hom["pairs"]] ==
        design["specs"]["count_homogeneity"]["pairs"],
        "rarefaction_size": runs["rarefaction"]["sizes_resolved"] if "sizes_resolved" in runs["rarefaction"] else
        sorted({e["size"] for s in runs["rarefaction"]["samples"] for e in s["estimates"]}),
        "pairs_compared": compared, "max_abs_difference": diffs, "holm_flags_agree": flags_agree,
        "max_abs_richness_difference": richness_diff,
    }
    (HERE / "study-check.json").write_text(json.dumps(check, indent=1) + "\n")
    print(json.dumps(check, indent=1))


if __name__ == "__main__":
    main()
