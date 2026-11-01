"""Declared delimited count tables give the same science as equivalent PAST input, and nothing is inferred or repaired."""

import json
from pathlib import Path

import pytest

from palaeo_agent import AnalysisError, calculate_permanova, inspect_study, reproduce_study, run, run_study
from palaeo_agent.community import calculate_community
from palaeo_agent.core import RmaSpec, calculate

TAXA = ["Globigerina bulloides", "Orbulina universa", "Neogloboquadrina incompta"]
ROWS = {"S1": [12, 3, 5], "S2": [4, 9, 1], "S3": [7, 7, 7], "S4": [1, 2, 15]}
ZONES = "sample_id,zone\nS1,A\nS2,A\nS3,B\nS4,B\n"


def past():
    return "\t".join([".", *TAXA]) + "\n" + "".join("\t".join([s, *map(str, v)]) + "\n" for s, v in ROWS.items())


def delimited(sep):
    return sep.join(["sample", *TAXA]) + "\n" + "".join(sep.join([s, *map(str, v)]) + "\n" for s, v in ROWS.items())


def community(path, **fmt):
    return {"method": "community", "input": str(path), "orientation": "samples_by_taxa", "value_type": "count",
            "transform": "none", "distance": "braycurtis", "dimensions": 1, "missing": "error",
            "empty_samples": "error", **fmt}


def results(outcome):
    return json.loads((Path(outcome["run_dir"]) / "results.json").read_text())


def test_community_formats_agree_and_keep_spaced_names(tmp_path):
    (tmp_path / "p.tsv").write_text(past())
    (tmp_path / "t.tsv").write_text(delimited("\t"))
    (tmp_path / "c.csv").write_text(delimited(","))
    reference = results(run(community(tmp_path / "p.tsv", format="past"), tmp_path / "rp"))
    assert reference["taxon_ids"] == TAXA
    for name, sep in (("t.tsv", "tab"), ("c.csv", "comma")):
        other = results(run(community(tmp_path / name, format="delimited", delimiter=sep), tmp_path / f"r{sep}"))
        assert other["distances"] == reference["distances"] and other["diversity"] == reference["diversity"]


def test_permanova_formats_agree():
    spec = {"method": "permanova", "orientation": "samples_by_taxa", "value_type": "count", "distance": "braycurtis",
            "transform": "relative_abundance", "missing": "error", "empty_samples": "error", "design": "independent",
            "permutation_scheme": "free", "permutations": 99, "seed": 1, "group_column": "zone", "input": "x", "metadata": "z"}
    a = calculate_permanova(dict(spec, format="past"), past().encode(), ZONES.encode())
    b = calculate_permanova(dict(spec, format="delimited", delimiter="comma"), delimited(",").encode(), ZONES.encode())
    assert a["pseudo_f"] == b["pseudo_f"] and a["r_squared"] == b["r_squared"]


def test_delimiter_is_declared_and_missing_is_refused(tmp_path):
    (tmp_path / "c.csv").write_text(delimited(",").replace(",15", ",NA"))
    with pytest.raises(ValueError):
        run(community(tmp_path / "c.csv", format="delimited"), tmp_path / "x")
    with pytest.raises(ValueError):
        run(community(tmp_path / "c.csv", format="past", delimiter="comma"), tmp_path / "y")
    with pytest.raises(AnalysisError) as missing:
        run(community(tmp_path / "c.csv", format="delimited", delimiter="comma"), tmp_path / "z")
    assert missing.value.code == "missing_counts"
    (tmp_path / "wrong.csv").write_text(delimited(","))
    with pytest.raises(AnalysisError) as wrong:
        run(community(tmp_path / "wrong.csv", format="delimited", delimiter="tab"), tmp_path / "w")
    assert wrong.value.code == "empty_taxa"


def test_study_reads_delimited_input_and_maps_spaced_names(tmp_path):
    (tmp_path / "c.csv").write_text(delimited(","))
    (tmp_path / "zones.csv").write_text(ZONES)
    spec = {"study_version": 1,
            "inputs": {"c": {"kind": "counts", "path": "c.csv", "format": "delimited", "delimiter": "comma",
                             "orientation": "samples_by_taxa"},
                       "z": {"kind": "metadata", "path": "zones.csv", "id_column": "sample_id"}},
            "datasets": {"d": {"source": "c", "metadata": "z", "operations": [
                {"op": "map_taxa", "mapping": {"Orbulina universa": "Globigerina bulloides"},
                 "reason": "synthetic merge"}]}},
            "analyses": [{"id": "a", "dataset": "d", "spec": community("x", format="past") | {"input": None}}]}
    del spec["analyses"][0]["spec"]["input"]
    outcome = run_study(spec, tmp_path / "study", base_dir=tmp_path)
    assert outcome["status"] == "complete", outcome


@pytest.mark.parametrize("text,code", [
    ("sample,A,B\n,1,2\nS2,3,5\nS3,6,1\n", "invalid_id"),
    ("sample,,B\nS1,1,2\nS2,3,5\nS3,6,1\n", "invalid_id"),
    ("sample,A,B\nS1,1,2\n,,\nS2,3,5\nS3,6,1\n", "invalid_id"),
    ('sample,A,B\nS1,1,2\nS2,3,5\nS3,6,"1', "invalid_delimited"),
    ("sample,A,B\nS1,1,2\nS2,3,NA\nS3,6,1\n", "missing_counts"),
    ("sample,A,B\nS1,1,2\nS2,3,\nS3,6,1\n", "missing_counts"),
])
def test_delimited_rejects_missing_labels_records_and_malformed_quotes(text, code):
    with pytest.raises(AnalysisError) as error:
        calculate_community(community("x", format="delimited", delimiter="comma"), text.encode())
    assert error.value.code == code


def test_delimited_missing_tokens_do_not_rename_labels():
    text = 'sample,NA," Taxon B "\nNA,1,2\n" S2 ",3,5\nS3,6,1\n'
    result = calculate_community(community("x", format="delimited", delimiter="comma"), text.encode())
    assert result["sample_ids"] == ["NA", " S2 ", "S3"]
    assert result["taxon_ids"] == ["NA", " Taxon B "]


def test_delimited_measurement_study_preserves_spaced_labels_and_reproduces(tmp_path):
    (tmp_path / "shells.csv").write_text(
        'sample,Shell length," Shell width "\nNA,10,5\n" Shell 2 ",20,12\nShell 3,30,20\n')
    spec = {"study_version": 1,
            "inputs": {"c": {"kind": "measurements", "path": "shells.csv", "format": "delimited",
                             "delimiter": "comma", "orientation": "samples_by_taxa"}},
            "datasets": {"d": {"source": "c"}},
            "analyses": [{"id": "a", "dataset": "d", "spec": {
                "method": "rma", "format": "past", "x": "Shell length", "y": " Shell width ",
                "transform": "none", "missing": "error"}}]}
    outcome = run_study(spec, tmp_path / "study", base_dir=tmp_path)
    assert outcome["status"] == "complete", outcome
    verified = inspect_study(outcome["study_dir"])
    result = json.loads((Path(outcome["study_dir"]) / verified["runs"]["a"]["run_dir"] / "results.json").read_text())
    assert [pair["sample_id"] for pair in result["pairs"]] == ["NA", " Shell 2 ", "Shell 3"]
    assert reproduce_study(outcome["study_dir"], tmp_path / "again")["status"] == "reproduced"


def test_past_rma_header_padding_and_exact_spaced_labels():
    spec = {"method": "rma", "input": "x", "format": "past", "x": "X", "y": "Y",
            "transform": "none", "missing": "error"}
    data = b".\tX\tY  \nS1\t10\t5\t \nS2\t20\t12\t \nS3\t30\t20\t \n"
    padded = calculate(RmaSpec.model_validate(spec), data)
    exact = calculate(RmaSpec.model_validate(spec | {"y": "Y  "}), data)
    plain = calculate(RmaSpec.model_validate(spec), data.replace(b"Y  ", b"Y").replace(b"\t \n", b"\n"))
    assert exact == plain
    assert {key: value for key, value in padded.items() if key != "warnings"} == {
        key: value for key, value in plain.items() if key != "warnings"}
    assert padded["warnings"] == [{"code": "padded_column_label",
                                   "message": "y selector 'Y' uses PAST header label 'Y  ' at data column 2"}]


@pytest.mark.parametrize("header,x,y,code", [
    (".\t X\tX \tY", "X", "Y", "ambiguous_column"),
    (".\t X \tY\tZ", " X ", "X", "same_column"),
])
def test_past_padding_never_chooses_ambiguous_or_duplicate_columns(header, x, y, code):
    spec = RmaSpec(method="rma", input="x", format="past", x=x, y=y, transform="none", missing="error")
    with pytest.raises(AnalysisError) as error:
        calculate(spec, (header + "\nS1\t1\t2\t3\nS2\t4\t5\t6\n").encode())
    assert error.value.code == code
