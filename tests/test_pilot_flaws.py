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
    work.mkdir()
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
