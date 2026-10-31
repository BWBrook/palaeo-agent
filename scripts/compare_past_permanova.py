"""Compare the declared native PAST one-way PERMANOVA deterministic export."""

import hashlib
import json
from pathlib import Path

from palaeo_agent.permanova import PermanovaSpec, calculate_permanova
from compare_past_captures import compare_values, execution_provenance


ROOT = Path(__file__).resolve().parents[1]
CAPTURE = ROOT / "references/past/captures/sprint2-permanova"


def compare():
    manifest = json.loads((CAPTURE / "capture.json").read_text())
    assert manifest["settings"] == {"similarity_index": "Bray-Curtis", "transform": "none",
        "permutations": 999, "repeated_measures": False,
        "groups": "samples1..5=A,6..10=B; synthetic validation grouping only", "group_column_type": "Group"}
    for item in manifest["outputs"]:
        data = (ROOT / item["path"]).read_bytes()
        assert len(data) == item["bytes"] and hashlib.sha256(data).hexdigest() == item["sha256"]
    source = json.loads((CAPTURE / "input-source.json").read_text())
    path = ROOT / source["source"]
    assert hashlib.sha256(path.read_bytes()).hexdigest() == source["sha256"]
    metadata = CAPTURE / "metadata.csv"
    spec = PermanovaSpec(method="permanova", input=path, metadata=metadata, group_column="group",
        format="past", orientation="taxa_by_samples", value_type="count", distance="braycurtis",
        transform="none", missing="error", empty_samples="error", design="independent",
        permutation_scheme="free", permutations=999, seed=20261031)
    result = calculate_permanova(spec, path.read_bytes(), metadata.read_bytes())
    fields = dict(line.split("\t", 1) for line in (CAPTURE / "raw/permanova.txt").read_text().splitlines() if "\t" in line)
    assert fields["Permutation N:"] == "999"
    labels = ["Total sum of squares:", "Within-group sum of squares:", "F:"]
    check = compare_values([[result[key]] for key in ("ss_total", "ss_within", "pseudo_f")],
        [[fields[label]] for label in labels], labels, ["value"], 4)
    return {**execution_provenance(), "comparison_script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "capture_manifest_sha256": hashlib.sha256((CAPTURE / "capture.json").read_bytes()).hexdigest(),
        "input_sha256": source["sha256"], "deterministic": check,
        "native_p": float(fields["p (same):"]), "native_permutations": 999,
        "python_exact_p": result["p_value"], "python_exact_denominator": result["permutation"]["denominator"],
        "p_scope": "Native stochastic p retained separately; schedules differ and p equality is not validated",
        "group_scope": "Synthetic grouping validates calculations only; no ecological group claim"}


if __name__ == "__main__":
    report = compare()
    (CAPTURE / "comparison.json").write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
    print(json.dumps(report["deterministic"], indent=2))
    raise SystemExit(0 if report["deterministic"]["status"] == "matched" else 1)
