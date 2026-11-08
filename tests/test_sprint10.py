import hashlib
import json
from pathlib import Path

import numpy as np
import pytest
from pydantic import ValidationError

from palaeo_agent import AnalysisError, inspect_run, run, run_study, inspect_study, reproduce_study
from palaeo_agent.community import calculate_community
from palaeo_agent.permanova import calculate_permanova

PCT = ".\tA\tB\tC\nS1\t50.5\t30.25\t19.25\nS2\t10\t60\t30\nS3\t0\t80.5\t19.5\nS4\t25\t25\t50\nS5\t70\t0\t30\nS6\t5.5\t44.5\t50\n"
META = "sample_id,band\nS1,high\nS2,high\nS3,high\nS4,low\nS5,low\nS6,low\n"
COMMUNITY = {"method": "community", "format": "past", "orientation": "samples_by_taxa", "value_type": "abundance",
             "transform": "none", "distance": "braycurtis", "dimensions": 2, "missing": "error", "empty_samples": "error"}
PERMANOVA = {"method": "permanova", "format": "past", "orientation": "samples_by_taxa", "value_type": "abundance",
             "transform": "relative_abundance", "distance": "braycurtis", "missing": "error", "empty_samples": "error",
             "design": "independent", "permutation_scheme": "free", "permutations": 999, "seed": 3,
             "group_column": "band"}


def _table(text, factors=None):
    rows = [line.split("\t") for line in text.strip().split("\n")]
    if factors:
        rows = [rows[0]] + [[r[0], *[repr(float(v) * f) for v in r[1:]]] for r, f in zip(rows[1:], factors)]
    return ("\n".join("\t".join(r) for r in rows) + "\n").encode()


def _community(data, **changes):
    return calculate_community(dict(COMMUNITY, input="x.dat", **changes), data)


def test_abundance_community_labels_weights_honestly():
    result = _community(_table(PCT))
    assert result["value_type"] == "abundance" and "retained_counts" not in result
    assert result["retained_values"][0] == [50.5, 30.25, 19.25]
    row = result["diversity"][0]
    assert "total" not in row and row["weight_sum"] == 100 and row["richness"] == 3
    p = np.array([50.5, 30.25, 19.25]) / 100
    assert row["shannon"] == pytest.approx(-(p * np.log(p)).sum(), rel=1e-12)
    assert row["simpson"] == pytest.approx(1 - (p**2).sum(), rel=1e-12)
    assert any("weights carry no specimen counts" in item for item in result["limitations"])


def test_common_factor_leaves_distances_and_diversity_unchanged():
    base = _community(_table(PCT))
    scaled = _community(_table(PCT, [0.01] * 6))
    assert np.allclose(base["distances"], scaled["distances"], rtol=0, atol=1e-12)
    for key in ("richness", "shannon", "simpson"):
        assert [r[key] for r in base["diversity"]] == pytest.approx([r[key] for r in scaled["diversity"]], rel=1e-12)


def test_row_specific_scaling_affects_raw_braycurtis_only_before_closure():
    factors = [1, 2, 0.5, 3, 1, 0.25]
    raw = (_community(_table(PCT)), _community(_table(PCT, factors)))
    assert not np.allclose(raw[0]["distances"], raw[1]["distances"])
    closed = [_community(_table(PCT, f), transform="relative_abundance") for f in (None, factors)]
    assert np.allclose(closed[0]["distances"], closed[1]["distances"], rtol=0, atol=1e-12)
    jaccard = [_community(_table(PCT, f), distance="jaccard", dimensions=1) for f in (None, factors)]
    assert jaccard[0]["distances"] == jaccard[1]["distances"]


@pytest.mark.parametrize("token", ["-1", "inf", "NaN", "1e-400", "1e400", "abc"])
def test_unsupported_abundance_tokens_are_refused(token):
    with pytest.raises(AnalysisError) as error:
        _community(_table(PCT.replace("50.5", token)))
    assert error.value.code == "invalid_abundance"


def test_empty_abundance_rows_follow_the_policy():
    data = _table(PCT.replace("S3\t0\t80.5\t19.5", "S3\t0\t0\t0.0"))
    with pytest.raises(AnalysisError) as error:
        _community(data)
    assert error.value.code == "empty_samples"
    assert [e["sample_id"] for e in _community(data, empty_samples="drop")["excluded"]] == ["S3"]


@pytest.mark.parametrize("method", ["rarefaction", "count_homogeneity"])
def test_count_only_methods_refuse_abundance_even_when_integer_valued(tmp_path, method):
    (tmp_path / "t.dat").write_text(".\tA\tB\nS1\t10\t5\nS2\t8\t7\n")
    spec = {"method": method, "input": str(tmp_path / "t.dat"), "format": "past", "orientation": "samples_by_taxa",
            "value_type": "abundance", "missing": "error", "empty_samples": "error"}
    if method == "count_homogeneity":
        spec.update(pairs=[["S1", "S2"]], simulations=999, seed=1)
    with pytest.raises((ValidationError, AnalysisError)):
        run(spec, tmp_path / "out")


def test_count_input_still_refuses_fractions_and_points_to_abundance():
    with pytest.raises(AnalysisError) as error:
        _community(_table(PCT), value_type="count")
    assert error.value.code == "invalid_count" and "abundance" in error.value.args[0]


def test_abundance_permanova_runs_and_inspects(tmp_path):
    (tmp_path / "p.dat").write_bytes(_table(PCT))
    (tmp_path / "m.csv").write_text(META)
    outcome = run(dict(PERMANOVA, input=str(tmp_path / "p.dat"), metadata=str(tmp_path / "m.csv")), tmp_path / "run")
    inspected = inspect_run(outcome["run_dir"])
    assert inspected["status"] == "verified"
    result = inspected["result"]
    assert result["value_type"] == "abundance" and "retained_counts" not in result
    assert (Path(outcome["run_dir"]) / "retained_values.csv").is_file()
    assert 0 < result["p_value"] <= 1 and 0 <= result["r_squared"] <= 1


def _rehash(run_dir, name):
    manifest_path = Path(run_dir) / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    data = (Path(run_dir) / name).read_bytes()
    manifest["files"][name].update(sha256=hashlib.sha256(data).hexdigest(), bytes=len(data))
    manifest_path.write_text(json.dumps(manifest, indent=2))


@pytest.mark.parametrize("tamper", [
    lambda r: r.update(value_type="count", retained_counts=r.pop("retained_values")),
    lambda r: r["retained_values"][0].__setitem__(0, 51.0),
    lambda r: r.update(transform="none"),
])
def test_inspection_binds_value_type_values_and_transform(tmp_path, tamper):
    (tmp_path / "c.dat").write_bytes(_table(PCT))
    outcome = run(dict(COMMUNITY, input=str(tmp_path / "c.dat"), transform="relative_abundance"), tmp_path / "run")
    results = Path(outcome["run_dir"]) / "results.json"
    data = json.loads(results.read_text())
    tamper(data)
    results.write_text(json.dumps(data, indent=2))
    _rehash(outcome["run_dir"], "results.json")
    with pytest.raises(Exception):
        inspect_run(outcome["run_dir"])


def _study(tmp_path, analyses, operations=()):
    (tmp_path / "p.dat").write_text(PCT.replace("\tC\n", "\tC1\n").replace(".\tA\tB", ".\tA\tB"))
    (tmp_path / "p.dat").write_text(".\tA\tB\tC1\tC2\n" + "".join(
        f"{r.split(chr(9))[0]}\t{r.split(chr(9))[1]}\t{r.split(chr(9))[2]}\t0.125\t{float(r.split(chr(9))[3]) - 0.125}\n"
        for r in PCT.strip().split("\n")[1:]))
    (tmp_path / "m.csv").write_text(META)
    return {"study_version": 1,
            "inputs": {"pct": {"kind": "abundance", "path": "p.dat", "orientation": "samples_by_taxa"},
                       "meta": {"kind": "metadata", "path": "m.csv", "id_column": "sample_id"}},
            "datasets": {"d": {"source": "pct", "metadata": "meta", "operations": list(operations)}},
            "analyses": analyses}


def test_study_merges_abundance_exactly_and_runs_end_to_end(tmp_path):
    spec = {k: v for k, v in PERMANOVA.items() if k not in ("input", "metadata")}
    study = _study(tmp_path, [{"id": "p", "dataset": "d", "spec": spec}],
                   [{"op": "map_taxa", "mapping": {"C1": "C", "C2": "C"}, "reason": "disjoint parts of one category"},
                    {"op": "exclude_taxa", "taxa": ["B"], "reason": "test exclusion; no renormalisation"}])
    outcome = run_study(study, tmp_path / "out", base_dir=tmp_path)
    assert outcome["status"] == "complete", outcome
    directory = Path(outcome["study_dir"])
    lines = (directory / "derived/d.dat").read_text().splitlines()
    assert lines[0] == ".\tA\tC" and lines[1] == "S1\t50.5\t19.250"
    assert inspect_study(directory)["status"] == "verified"
    assert reproduce_study(directory, tmp_path / "again")["status"] == "reproduced"


@pytest.mark.parametrize("method_spec", [
    {"method": "rarefaction", "format": "past", "orientation": "samples_by_taxa", "value_type": "count",
     "missing": "error", "empty_samples": "error"},
    dict(COMMUNITY, value_type="count"),
])
def test_study_binds_abundance_inputs_to_abundance_methods(tmp_path, method_spec):
    study = _study(tmp_path, [{"id": "x", "dataset": "d", "spec": method_spec}])
    with pytest.raises(AnalysisError) as error:
        run_study(study, tmp_path / "out", base_dir=tmp_path)
    assert error.value.code == "invalid_study"


def test_counts_inputs_refuse_abundance_declarations(tmp_path):
    (tmp_path / "c.dat").write_text(".\tA\tB\nS1\t1\t2\nS2\t3\t4\nS3\t2\t2\n")
    study = {"study_version": 1, "inputs": {"c": {"kind": "counts", "path": "c.dat", "orientation": "samples_by_taxa"}},
             "datasets": {"d": {"source": "c"}},
             "analyses": [{"id": "x", "dataset": "d", "spec": dict(COMMUNITY, dimensions=1)}]}
    with pytest.raises(AnalysisError) as error:
        run_study(study, tmp_path / "out", base_dir=tmp_path)
    assert error.value.code == "invalid_study"


OVERFLOW = ".\tA\tB\nx\t1e308\t0\ny\t1e308\t1e307\nz\t0\t1\n"


@pytest.mark.parametrize("entry", ["validate", "run"])
@pytest.mark.parametrize("table", [OVERFLOW, ".\tA\tB\nx\t1e308\t1e308\ny\t1\t2\nz\t2\t1\n"])
def test_abundance_range_is_refused_in_validation_and_execution(tmp_path, entry, table):
    from palaeo_agent import validate
    (tmp_path / "o.dat").write_text(table)
    spec = dict(COMMUNITY, input=str(tmp_path / "o.dat"), dimensions=1)
    for method_spec in (spec, dict(PERMANOVA, input=spec["input"], transform="none", metadata=None)):
        method_spec = {k: v for k, v in method_spec.items() if v is not None}
        if method_spec["method"] == "permanova":
            (tmp_path / "m.csv").write_text("sample_id,band\nx,a\ny,a\nz,b\n")
            method_spec["metadata"] = str(tmp_path / "m.csv")
        with pytest.raises(AnalysisError) as error:
            validate(method_spec) if entry == "validate" else run(method_spec, tmp_path / f"out-{method_spec['method']}")
        assert error.value.code == "abundance_range"


def test_rescaled_overflow_table_gives_the_exact_distance():
    rescaled = _community(OVERFLOW.replace("1e308", "1").replace("1e307", "0.1").replace("z\t0\t1", "z\t0\t1e-308").encode(),
                          dimensions=1)
    assert rescaled["distances"][0][1] == pytest.approx(1 / 21, rel=1e-15)


def test_community_distances_refuses_rows_outside_the_range():
    from palaeo_agent.community import community_distances
    with pytest.raises(AnalysisError) as error:
        community_distances(np.array([[1e308, 0.0], [1e308, 1e307], [0.0, 1.0]]), transform="none", distance="braycurtis")
    assert error.value.code == "abundance_range"


def test_native_positive_weights_may_not_underflow_or_overflow():
    from fractions import Fraction
    from palaeo_agent import analyse_community
    common = dict(sample_ids=["A", "B", "C"], taxon_ids=["x", "y", "z"], value_type="abundance", transform="none",
                  distance="jaccard", dimensions=1, empty_samples="error")
    for tiny in (Fraction(1, 10**400), Fraction(10**400)):
        with pytest.raises(AnalysisError) as error:
            analyse_community([[tiny, 1, 0], [1, 0, 0], [0, 1, 1]], **common)
        assert error.value.code == "invalid_abundance"
    with pytest.raises(AnalysisError) as error:
        analyse_community([[1e308, 1e308, 0], [1, 0, 0], [0, 1, 1]], **common)
    assert error.value.code == "abundance_range"
    ok = analyse_community([[Fraction(1, 10**300), 1, 0], [1, 0, 0], [0, 1, 1]], **common)
    assert ok["diversity"][0]["richness"] == 2 and ok["distances"][0][1] == 0.5
