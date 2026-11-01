"""Representative two-format demonstrations of the frozen reviewer flaws.

For a preparation flaw (P01), a design flaw (P12) and an interpretation flaw
(P10), an intact package is built in each format: a toolkit study bundle and a
direct script. The flaw is then planted by the per-format route the protocol
prescribes, and the flawed package must reproduce the frozen reference values
and still pass its own integrity check.
"""

import json
from pathlib import Path
import subprocess
import sys

import pytest

from palaeo_agent import inspect_study, run_study

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "evaluation/pilot"))
import flaws  # noqa: E402

FROZEN = json.loads((ROOT / "evaluation/pilot/flaws.json").read_text())
ITEMS = ROOT / "evaluation/pilot/items"
COMMUNITY = {"method": "community", "format": "past", "orientation": "samples_by_taxa", "value_type": "count",
             "transform": "none", "distance": "braycurtis", "dimensions": 1, "missing": "error", "empty_samples": "error"}
PERMANOVA = {"method": "permanova", "format": "past", "orientation": "samples_by_taxa", "value_type": "count",
             "distance": "braycurtis", "transform": "relative_abundance", "missing": "error", "empty_samples": "error",
             "design": "independent", "permutation_scheme": "free", "permutations": 99, "seed": 3, "group_column": "zone"}
P01_SCRIPT = '''import itertools, json
rows = [l.split() for l in open("materials/counts.tsv") if l.strip()]
cores = rows[0][1:]
counts = {c: [int(r[i + 1]) for r in rows[1:]] for i, c in enumerate(cores)}
EXCLUDE = []
kept = [c for c in cores if c not in EXCLUDE]
bc = lambda a, b: sum(abs(x - y) for x, y in zip(a, b)) / (sum(a) + sum(b))
pairs = list(itertools.combinations(kept, 2))
mean = sum(bc(counts[a], counts[b]) for a, b in pairs) / len(pairs)
json.dump({"status": "completed", "results": {"mean_bray_curtis": mean, "n_cores": len(kept)}, "assumptions": [],
           "exclusions": [{"id": c, "reason": "residue lost before counting"} for c in EXCLUDE], "issues": [],
           "summary": "Mean pairwise Bray-Curtis on raw counts."}, open("answer.json", "w"))
'''


def toolkit_package(tmp_path, item, analysis, operations=()):
    m = ITEMS / item / "materials"
    inputs = {"c": {"kind": "counts", "path": str(m / "counts.tsv"),
                    "orientation": "taxa_by_samples" if item.startswith("P01") else "samples_by_taxa"}}
    dataset = {"source": "c", "operations": list(operations)}
    if analysis["method"] == "permanova":
        inputs["z"] = {"kind": "metadata", "path": str(m / "zones.csv"), "id_column": "sample"}
        dataset["metadata"] = "z"
    outcome = run_study({"study_version": 1, "inputs": inputs, "datasets": {"d": dataset},
                         "analyses": [{"id": "a", "dataset": "d", "spec": analysis}]}, tmp_path / "study")
    verified = inspect_study(outcome["study_dir"])
    return verified, json.loads((Path(outcome["study_dir"]) / verified["runs"]["a"]["run_dir"] / "results.json").read_text())


def direct_package(tmp_path, item, script):
    work = tmp_path / "direct"
    work.mkdir(parents=True)
    (work / "materials").symlink_to(ITEMS / item / "materials")
    (work / "analysis.py").write_text(script)
    subprocess.run([sys.executable, "analysis.py"], cwd=work, check=True)
    return work, json.loads((work / "answer.json").read_text())


def rerun_reproduces(work):
    before = json.loads((work / "answer.json").read_text())
    subprocess.run([sys.executable, "analysis.py"], cwd=work, check=True)
    return json.loads((work / "answer.json").read_text()) == before


def test_preparation_flaw_in_both_formats(tmp_path):
    flaw = FROZEN["P01-control"]
    _, intact = toolkit_package(tmp_path / "t0", "P01-control", COMMUNITY)
    import numpy as np
    d = np.array(intact["distances"])
    assert not flaws.results_match({"mean_bray_curtis": d[np.triu_indices(len(d), 1)].mean()}, flaw["results"])
    verified, flawed = toolkit_package(tmp_path / "t1", "P01-control", COMMUNITY, [
        {"op": "exclude", "samples": ["5"], "reason": "residue lost before counting"}])
    d = np.array(flawed["distances"])
    assert verified["status"] == "verified"
    assert flaws.results_match({"mean_bray_curtis": d[np.triu_indices(len(d), 1)].mean(), "n_cores": flawed["n"]},
                               flaw["results"])
    work, _ = direct_package(tmp_path, "P01-control", P01_SCRIPT.replace('EXCLUDE = []', 'EXCLUDE = ["5"]'))
    answer = json.loads((work / "answer.json").read_text())
    assert rerun_reproduces(work) and flaws.results_match(answer["results"], flaw["results"])
    assert answer["exclusions"] == flaw["answer_edits"]["exclusions"]


def test_design_flaw_in_toolkit_format(tmp_path):
    flaw = FROZEN["P12-control"]
    verified, flawed = toolkit_package(tmp_path, "P12-control", dict(PERMANOVA, transform="none"))
    assert verified["status"] == "verified"
    assert flaws.results_match({k: flawed[k] for k in ("pseudo_f", "r_squared", "n")}, flaw["results"])


def test_interpretation_flaw_leaves_numbers_and_integrity(tmp_path):
    flaw = FROZEN["P10-control"]
    intact = {"status": "completed", "results": json.loads((ITEMS / "P10-control/key.json").read_text())["results"],
              "assumptions": [], "exclusions": [], "issues": [], "summary": "Youngest minus oldest Shannon."}
    flawed = flaws.apply_answer_edits(intact, flaw)
    assert flawed["results"] == intact["results"] and flawed["results"]["shannon_change"] > 0
    assert flawed["summary"].endswith("declined from the oldest to the youngest sample.")


@pytest.mark.parametrize("item", sorted(FROZEN))
def test_frozen_values_regenerate(item):
    assert flaws.results_match(flaws.frozen()[item]["results"], FROZEN[item]["results"], tolerance=1e-12)


P12_SCRIPT = '''import csv, itertools, json
rows = [l.split() for l in open("materials/counts.tsv") if l.strip()]
ids = [r[0] for r in rows[1:]]
counts = [[int(v) for v in r[1:]] for r in rows[1:]]
zones = {r["sample"]: r["zone"] for r in csv.DictReader(open("materials/zones.csv"))}
TRANSFORM = "relative"
data = [[v / sum(c) for v in c] for c in counts] if TRANSFORM == "relative" else counts
bc = lambda a, b: sum(abs(x - y) for x, y in zip(a, b)) / (sum(a) + sum(b))
groups = [zones[i] for i in ids]
n = len(ids)
d2 = {(i, j): bc(data[i], data[j]) ** 2 for i, j in itertools.combinations(range(n), 2)}
sst = sum(d2.values()) / n
labels = sorted(set(groups))
ssw = sum(sum(v for (i, j), v in d2.items() if groups[i] == groups[j] == g) / groups.count(g) for g in labels)
a = len(labels)
f = ((sst - ssw) / (a - 1)) / (ssw / (n - a))
json.dump({"status": "completed", "results": {"pseudo_f": f, "r_squared": (sst - ssw) / sst, "n": n},
           "assumptions": [], "exclusions": [], "issues": [], "summary": "Descriptive PERMANOVA statistics."},
          open("answer.json", "w"))
'''
P10_SCRIPT = '''import json, math
rows = [l.split() for l in open("materials/counts.tsv") if l.strip()]
h = lambda c: -sum(v / sum(c) * math.log(v / sum(c)) for v in c if v)
counts = {r[0]: [int(v) for v in r[1:]] for r in rows[1:]}
CLAIM = ""
change = h(counts["S12"]) - h(counts["S1"])
json.dump({"status": "completed", "results": {"shannon_change": change}, "assumptions": [], "exclusions": [],
           "issues": [], "summary": ("S1 is the lowest, oldest sample. " + CLAIM).strip()}, open("answer.json", "w"))
'''


def test_design_flaw_in_direct_format(tmp_path):
    flaw = FROZEN["P12-control"]
    intact_dir, intact = direct_package(tmp_path / "a", "P12-control", P12_SCRIPT)
    assert not flaws.results_match(intact["results"], flaw["results"])
    work, flawed = direct_package(tmp_path / "b", "P12-control", P12_SCRIPT.replace('TRANSFORM = "relative"', 'TRANSFORM = "raw"'))
    assert rerun_reproduces(work) and flaws.results_match(flawed["results"], flaw["results"])


def test_interpretation_flaw_persists_in_saved_packages(tmp_path):
    flaw = FROZEN["P10-control"]
    claim = flaw["answer_edits"]["summary_append"]
    work, answer = direct_package(tmp_path / "direct", "P10-control", P10_SCRIPT.replace('CLAIM = ""', f'CLAIM = {claim!r}'))
    assert rerun_reproduces(work) and answer["summary"].endswith(claim)
    assert flaws.results_match(answer["results"], flaw["results"])
    m = ITEMS / "P10-control/materials"
    outcome = run_study({"study_version": 1, "inputs": {"c": {"kind": "counts", "path": str(m / "counts.tsv"),
                                                              "orientation": "samples_by_taxa"}},
                         "datasets": {"d": {"source": "c"}}, "analyses": [{"id": "a", "dataset": "d", "spec": COMMUNITY}]},
                        tmp_path / "toolkit/study")
    record = json.loads((Path(outcome["study_dir"]) / inspect_study(outcome["study_dir"])["runs"]["a"]["run_dir"]
                         / "results.json").read_text())
    shannon = {row["sample_id"]: row["shannon"] for row in record["diversity"]}
    intact = {"status": "completed", "results": {"shannon_change": shannon["S12"] - shannon["S1"]}, "assumptions": [],
              "exclusions": [], "issues": [], "summary": "Toolkit community run; S1 is oldest."}
    saved = tmp_path / "toolkit/answer.json"
    saved.write_text(json.dumps(flaws.apply_answer_edits(intact, flaw)))
    reloaded = json.loads(saved.read_text())
    assert inspect_study(outcome["study_dir"])["status"] == "verified"
    assert reloaded["summary"].endswith(claim) and flaws.results_match(reloaded["results"], flaw["results"])
