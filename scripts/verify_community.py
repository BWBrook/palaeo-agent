"""Check the frozen R references and record the development sensitivity workflow."""

import hashlib
import json
from pathlib import Path
import subprocess
import sys

import numpy as np

from palaeo_agent import CommunitySpec, compare_community_runs, inspect_comparison, inspect_run, run
from palaeo_agent.community import calculate_community


root = Path(__file__).resolve().parents[1]
output = root / "runs/community-verification"
reference = json.loads((root / "benchmarks/past/references/community-base-r.json").read_text())
data_path = root / reference["input"]
data = data_path.read_bytes()
assert hashlib.sha256(data).hexdigest() == reference["input_sha256"]
checks = []
for expected in reference["cases"]:
    spec = CommunitySpec(method="community", input=data_path, format="past", orientation="taxa_by_samples",
                         value_type="count", transform=expected["transform"], distance=expected["distance"],
                         dimensions=2, missing="error", empty_samples="error")
    result = calculate_community(spec, data)
    errors = {}
    for field in ("distances", "eigenvalues", "positive_gram"):
        np.testing.assert_allclose(result[field], expected[field], rtol=reference["rtol"], atol=reference["atol"])
        errors[field] = float(np.max(np.abs(np.asarray(result[field]) - np.asarray(expected[field]))))
    for actual, target in zip(result["diversity"], expected["diversity"], strict=True):
        assert actual["sample_id"] == target["sample_id"]
        for field in ("total", "richness", "shannon", "simpson"):
            np.testing.assert_allclose(actual[field], target[field], rtol=reference["rtol"], atol=reference["atol"])
    checks.append({"transform": spec.transform, "distance": spec.distance, "maximum_absolute_errors": errors})


def load_spec(name):
    path = root / f"examples/community-llanvirn-{name}.json"
    values = json.loads(path.read_text())
    for key in ("input", "metadata"):
        values[key] = (path.parent / values[key]).resolve()
    return CommunitySpec.model_validate(values)


baseline = run(load_spec("relative"), output)
sensitivity = run(load_spec("raw"), output)
comparison = compare_community_runs(baseline["run_dir"], sensitivity["run_dir"], output)
verified = inspect_comparison(comparison["comparison_dir"])
reproductions = []
for name in ("baseline", "sensitivity"):
    child = Path(comparison["comparison_dir"]) / name
    response = subprocess.run([sys.executable, "-m", "palaeo_agent", "reproduce", str(child),
                               "--output", str(output)], capture_output=True, text=True, check=True)
    record = json.loads(response.stdout)
    assert record["status"] == "reproduced" and not record["differences"]
    reproductions.append({"arm": name, "status": record["status"], "differences": record["differences"],
                          "environment_identical": record["environment_identical"]})
evidence = {"development_only": True, "plan_commit": "228aa27",
            "input_sha256": reference["input_sha256"], "R_reference": reference["reference_kind"],
            "comparisons": checks, "fresh_process_reproductions": reproductions,
            "comparison": comparison["summary"], "PAST_numerical_runs": 0}
(root / "benchmarks/past/references/community-verification.json").write_text(json.dumps(evidence, indent=2) + "\n")
print(json.dumps({"comparison_dir": comparison["comparison_dir"], "reference_cases": len(checks),
                  "reproductions": reproductions, "summary": comparison["summary"]}))
