"""Rerun with: python analyse.py (uses installed packages; no network)."""
import csv
import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def validate(value, schema):
    """Validate the subset of JSON Schema used by the supplied contract."""
    types = {"object": dict, "array": list, "string": str}
    if "type" in schema:
        assert isinstance(value, types[schema["type"]])
    if "enum" in schema:
        assert value in schema["enum"]
    if isinstance(value, dict):
        assert set(schema.get("required", [])) <= set(value)
        properties = schema.get("properties", {})
        if schema.get("additionalProperties") is False:
            assert set(value) <= set(properties)
        for key, item in value.items():
            if key in properties:
                validate(item, properties[key])
    if isinstance(value, list) and "items" in schema:
        for item in value:
            validate(item, schema["items"])


def main():
    with (ROOT / "counts.tsv").open() as handle:
        rows = list(csv.reader(handle, delimiter="\t"))
    ids = [row[0] for row in rows[1:]]
    counts = [[int(value) for value in row[1:]] for row in rows[1:]]
    with (ROOT / "samples.csv").open() as handle:
        metadata = list(csv.DictReader(handle))
    assert len(ids) == len(set(ids)) == 10
    assert len(metadata) == len({row["sample_id"] for row in metadata}) == 10
    assert set(ids) == {row["sample_id"] for row in metadata}
    assert len({row["site_id"] for row in metadata}) == 10
    assert len(rows[0][1:]) == len(set(rows[0][1:])) == 2
    assert all(len(row) == 2 and min(row) >= 0 and sum(row) > 0 for row in counts)

    completed = subprocess.run(
        [sys.executable, "-m", "palaeo_agent", "run", "permanova_spec.json",
         "--output", "permanova_run"],
        cwd=ROOT, text=True, capture_output=True, check=True,
    )
    run = json.loads(completed.stdout)
    run_dir = Path(run["run_dir"])
    result = json.loads((run_dir / "results.json").read_text())
    permutation = result["permutation"]
    assert permutation["mode"] == "exact"
    assert permutation["space_size"] == permutation["draws"] == 210
    assert permutation["count_extreme"] == 8
    assert result["excluded"] == []

    keys = ["n", "pseudo_f", "r_squared", "p_value", "ss_total", "ss_within",
            "ss_between", "df_between", "df_within"]
    results = {key: result[key] for key in keys}
    results["group_mean_centroid_distance"] = result["dispersion"]["group_mean_distances"]
    results["claim_supported"] = 0
    answer = {
        "status": "completed",
        "results": results,
        "assumptions": [
            "Each sample row represents one distinct site sampled once; the ten sites are independent sampling units, as explicitly stated in dictionary.md.",
            "Facies labels are freely exchangeable under the null, as stated in dictionary.md; there are no blocks, covariates, repeated observations or nested subsamples. These design assumptions cannot be established from the counts alone.",
            "Counts are specimen counts with samples in rows and taxa in columns. Bray-Curtis dissimilarities use the original counts without transformation, normalization or aggregation."
        ],
        "exclusions": [],
        "issues": [
            "No missing, negative or noninteger counts, empty samples, duplicate sample/taxon IDs, unmatched metadata records or repeated site IDs were found. All ten sites and both taxa were retained. S10 was retained; its different composition is not evidence of a data error.",
            "Group sizes are unequal (reef 4; lagoon 6). Palaeo-Agent warns that unequal group sizes complicate interpretation of location and dispersion. Mean centroid distances show substantially greater lagoon spread; these are descriptive and do not establish a significant dispersion difference.",
            "Centroid distances have no bias adjustment, square-root distance transformation or additive correction. One positive principal-coordinate axis was retained; nine numerical near-zero eigenmodes were discarded using the recorded tolerance. No substantive negative axis or negative squared centroid distance was found.",
            "No dispersion significance test was performed, as requested. PERMANOVA is a distance-based group association test and does not isolate a pure centroid-location effect or rule out dispersion contributions."
        ],
        "summary": (
            "Palaeo-Agent performed one-way PERMANOVA on untransformed counts using Bray-Curtis dissimilarity. "
            "Seed 20261031 and 999 requested permutations were specified; all 210 distinct allocations preserving "
            "group sizes were enumerated, including the observed allocation. Eight statistics were at least as "
            "extreme as observed (using the package tie tolerance), giving exact p = 8/210 = "
            + str(result["p_value"]) + ". At alpha 0.05 this supports a facies-associated difference in community "
            "composition. The exact draft claim is not supported (claim_supported = 0): although observed centroids "
            "differ, this test cannot establish a pure centroid-location difference, and it cannot show that "
            "within-facies spread differences cannot explain the significant result. The lagoon has much greater "
            "descriptive mean centroid distance than the reef, and sample sizes are unequal. No causal inference "
            "is warranted. Rerun with python analyse.py; permanova_spec.json and the package run directory "
            "record the specification, full results, permutation allocations/statistics, input copies, environment "
            "and manifest. provenance.json identifies the run used for this answer and input SHA-256 hashes."
        ),
    }
    schema = json.loads((ROOT / "answer.schema.json").read_text())
    validate(answer, schema)
    assert set(results) == set(keys + ["group_mean_centroid_distance", "claim_supported"])
    (ROOT / "answer.json").write_text(json.dumps(answer, indent=2, allow_nan=False) + "\n")
    provenance = {
        "command": "python analyse.py",
        "run_directory": str(run_dir.relative_to(ROOT)),
        "python_version": sys.version,
        "sha256": {
            name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
            for name in ["task.md", "dictionary.md", "counts.tsv", "samples.csv",
                         "answer.schema.json", "permanova_spec.json", "analyse.py"]
        },
    }
    (ROOT / "provenance.json").write_text(json.dumps(provenance, indent=2) + "\n")
    print(json.dumps({"validated": True, "results": results}, indent=2))


if __name__ == "__main__":
    main()
