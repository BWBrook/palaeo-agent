"""Check supported item outputs against independent keys; never generate keys."""

import argparse
from collections import Counter
import csv
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile

from palaeo_agent import PermanovaSpec, calculate_permanova, validate

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
NUMERICAL_FIELDS = ("n", "pseudo_f", "r_squared", "p_value", "ss_total", "ss_within", "ss_between",
                    "df_between", "df_within")


def request(materials):
    return {"method": "permanova", "input": str(materials / "counts.tsv"),
            "metadata": str(materials / "samples.csv"), "group_column": "facies", "format": "past",
            "orientation": "samples_by_taxa", "value_type": "count", "distance": "braycurtis",
            "transform": "none", "missing": "error", "empty_samples": "error", "design": "independent",
            "permutation_scheme": "free", "permutations": 999, "seed": 20261031}


def compare(expected, actual, path=""):
    if isinstance(expected, dict):
        if not isinstance(actual, dict) or set(expected) != set(actual):
            return [path or "results keys"]
        return [failure for name in expected for failure in compare(expected[name], actual[name], f"{path}.{name}")]
    if isinstance(expected, int):
        return [] if actual == expected else [path]
    return [] if abs(actual - expected) <= max(1e-10, abs(expected) * 1e-10) else [path]


def check_item(item_dir):
    materials = item_dir / "materials"
    spec = request(materials)
    with (materials / "samples.csv").open() as stream:
        metadata = list(csv.DictReader(stream))
    sites = Counter(row["site_id"] for row in metadata)
    dependent = any(count > 1 for count in sites.values()) and "not independent" in (materials / "dictionary.md").read_text()
    if dependent:
        spec["design"] = "dependent_subsamples"
        with tempfile.TemporaryDirectory(prefix="palaeo-sprint2-design-") as temp:
            path = Path(temp) / "spec.json"
            path.write_text(json.dumps(spec))
            result = subprocess.run([sys.executable, "-m", "palaeo_agent", "validate", str(path)],
                                    cwd="/", capture_output=True, text=True, check=False)
        error = json.loads(result.stderr)
        if result.returncode != 2 or error.get("code") != "invalid_specification":
            raise AssertionError("dependent design was not rejected through the structured CLI contract")
        return {"item": item_dir.name, "status": "supported_stop", "error_code": error["code"],
                "shared_site_ids": sorted(site for site, count in sites.items() if count > 1),
                "scope": "Sampling description supplies dependence; the toolkit cannot infer independence from labels."}
    validate(spec)
    model = PermanovaSpec.model_validate(spec)
    result = calculate_permanova(model, (materials / "counts.tsv").read_bytes(), (materials / "samples.csv").read_bytes())
    actual = {name: result[name] for name in NUMERICAL_FIELDS}
    actual["group_mean_centroid_distance"] = result["dispersion"]["group_mean_distances"]
    task = (materials / "task.md").read_text()
    if "claim_supported" in task:
        actual["claim_supported"] = 0 if "cannot explain" in task else int(result["p_value"] <= 0.05)
    key = json.loads((item_dir / "key.json").read_text())
    differences = compare(key["results"], actual)
    if differences:
        raise AssertionError(f"{item_dir.name}: reference disagreements: {differences}")
    return {"item": item_dir.name, "status": "agrees", "results": actual,
            "mode": result["permutation"]["mode"], "allocations": result["permutation"]["space_size"],
            "scope": "Numerics checked against standalone rational keys; supplied-claim judgment uses declared method scope."}


def check():
    rows = [check_item(path) for path in sorted((HERE / "items").iterdir()) if path.is_dir()]
    return {"bank_version": "sprint2-group-bank-v1", "passed": len(rows) == 6,
            "python": sys.version.split()[0], "python_executable": sys.executable,
            "source_sha256": {str(path.relative_to(REPO)): hashlib.sha256(path.read_bytes()).hexdigest()
                              for path in sorted((REPO / "src").rglob("*.py"))},
            "generator_sha256": hashlib.sha256((HERE / "build_items.py").read_bytes()).hexdigest(),
            "key_sha256": {str(path.relative_to(HERE)): hashlib.sha256(path.read_bytes()).hexdigest()
                           for path in sorted((HERE / "items").glob("*/key.json"))}, "items": rows}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = check()
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
