import csv
import copy
import hashlib
import json
import shutil
from pathlib import Path

import pytest

from palaeo_agent import AnalysisError, inspect_neotoma, neotoma_extract, reproduce_neotoma
from palaeo_agent.cli import main as cli_main

ROOT = Path(__file__).resolve().parents[1]
SURFACE = ROOT / "analyses/tas-surface/source/neotoma-tas-surface-download.json"
SELINA = ROOT / "analyses/lake-selina/source/neotoma-52767-download.json"
SURFACE_IDS = [74429, 75430, 74914, 74643, 74779, 74795, 74778, 74764, 74160, 74142, 74304, 74699, 74569, 74618,
               74701, 74780, 73988, 74777, 74303, 74141, 75423, 74644, 74798, 74766, 75421]


def _datum(label, value, units="NISP", element="pollen", group="TRSH", taxonid=1, **extra):
    return {"variablename": label, "value": value, "units": units, "element": element, "ecologicalgroup": group,
            "taxonid": taxonid, "elementtype": element, "taxongroup": "Vascular plants", **extra}


def _download():
    point = json.dumps({"type": "Point", "coordinates": [146.5, -42.1]})
    polygon = json.dumps({"type": "Polygon", "coordinates": [[[145, -41], [146, -41], [146, -42], [145, -41]]]})

    def record(dataset_id, site_id, sitename, geography, samples, default=10):
        return {"site": {"siteid": site_id, "sitename": sitename, "altitude": 700, "geography": geography,
                         "collectionunit": {"collectionunitid": site_id * 10, "handle": f"H{site_id}", "notes": None,
                                            "defaultchronology": default, "depositionalenvironment": "Bog",
                                            "collunittype": "Core",
                                            "dataset": {"datasetid": dataset_id, "datasetname": f"D{dataset_id}",
                                                        "doi": [f"10.1/{dataset_id}"],
                                                        "datasetpi": [{"contactname": "PI, A", "contactid": 9}],
                                                        "samples": samples}}}}

    def sample(sid, depth, data, ages=()):
        return {"sampleid": sid, "depth": depth, "thickness": None, "samplename": None, "analysisunitname": None,
                "samplenotes": None, "datum": data, "ages": list(ages)}

    age = lambda c, a, lo=None: {"chronologyid": c, "chronologyname": f"C{c}", "agetype": "cal BP", "age": a,
                                 "ageolder": lo, "ageyounger": None}
    return {"status": "success", "message": "", "data": [
        record(1, 100, "Alpha", point, [
            sample(12, 20, [_datum("Pinus", 5), _datum("Poaceae", 3, group="UPHE", taxonid=2),
                            _datum("Sphagnum", 9, element="spore", group="VACR", taxonid=3)], [age(10, 200, 250), age(11, 210)]),
            sample(11, 10, [_datum("Pinus", 2)], [age(10, 100)]),
            sample(13, 30, [_datum("Sphagnum", 4, element="spore", group="VACR", taxonid=3)])]),
        record(2, 200, "Beta", point, [sample(21, 0, [_datum("Poaceae", 7, group="UPHE", taxonid=2)])]),
        record(3, 300, "Gamma", polygon, [sample(31, 5, [_datum("Pinus", 1.5, units="percent")])]),
    ]}


def _write(tmp_path, document, name="download.json"):
    data = json.dumps(document).encode()
    path = tmp_path / name
    path.write_bytes(data)
    return path, hashlib.sha256(data).hexdigest()


def _spec(path, digest, **changes):
    return {"source": str(path), "source_sha256": digest, "datasets": [1, 2], "units": "NISP",
            "elements": ["pollen"], "ecological_groups": ["TRSH", "UPHE"], "absent_taxa": "zero",
            "row_order": "source", **changes}


def _extract(tmp_path, document=None, **changes):
    path, digest = _write(tmp_path, document or _download())
    return neotoma_extract(_spec(path, digest, **changes), tmp_path / "out")


def _rows(path):
    return list(csv.DictReader(open(path, encoding="utf-8")))


def test_synthetic_extraction_fills_zeros_keeps_ids_and_encodes_metadata(tmp_path):
    out = _extract(tmp_path)
    bundle = Path(out["bundle"])
    assert out["kind"] == "counts" and out["all_zero_samples"] == ["13"]
    assert (bundle / "table.tsv").read_text() == "sample_id\tPinus\tPoaceae\n12\t5\t3\n11\t2\t0\n13\t0\t0\n21\t0\t7\n"
    samples = _rows(bundle / "samples.csv")
    assert [s["sample_id"] for s in samples] == ["12", "11", "13", "21"]
    first = samples[0]
    assert first["thickness"] == "" and first["samplename"] == "" and first["collectionunit_notes"] == ""
    assert first["doi"] == '["10.1/1"]'
    assert first["dataset_pi"] == '[{"contactid":9,"contactname":"PI, A"}]'
    assert (first["geometry_type"], first["lon"], first["lat"]) == ("Point", "146.5", "-42.1")
    assert first["shares_coordinates_with"] == "Beta" and samples[3]["shares_coordinates_with"] == "Alpha"
    ages = _rows(bundle / "ages.csv")
    assert [(a["sample_id"], a["chronologyid"], a["is_default_chronology"], a["ageyounger"]) for a in ages] == [
        ("12", "10", "true", ""), ("12", "11", "false", ""), ("11", "10", "true", "")]
    assert ages[0]["ageolder"] == "250"
    taxa = _rows(bundle / "taxa.csv")
    assert [(t["label"], t["taxonid"], t["ecologicalgroup"], t["n_samples_positive"]) for t in taxa] == [
        ("Pinus", "1", "TRSH", "2"), ("Poaceae", "2", "UPHE", "2")]
    record = json.loads((bundle / "extract.json").read_text())
    assert record["dropped"] == [{"element": "spore", "ecologicalgroup": "VACR", "units": "NISP", "n": 2}]
    assert record["specification"]["source"] == "source.json"
    assert inspect_neotoma(bundle)["status"] == "verified"


def test_depth_order_and_polygon_geometry(tmp_path):
    out = _extract(tmp_path, row_order="depth")
    assert [s["sample_id"] for s in _rows(Path(out["bundle"]) / "samples.csv")] == ["11", "12", "13", "21"]
    (tmp_path / "p").mkdir()
    poly = _extract(tmp_path / "p", datasets=[3], units="percent")
    row = _rows(Path(poly["bundle"]) / "samples.csv")[0]
    assert (row["geometry_type"], row["lon"], row["lat"]) == ("Polygon", "", "")
    assert poly["kind"] == "abundance"


def _mutate(change):
    document = _download()
    change(document)
    return document


@pytest.mark.parametrize("change,specchanges,code", [
    (lambda d: None, {"datasets": "all"}, "mixed_units"),
    (lambda d: None, {"datasets": [1, 9]}, "unknown_dataset"),
    (lambda d: d["data"].append(copy.deepcopy(d["data"][1])), {}, "duplicate_dataset"),
    (lambda d: d["data"][1]["site"]["collectionunit"]["dataset"]["samples"][0].update(sampleid=12), {}, "duplicate_sample"),
    (lambda d: d["data"][0]["site"]["collectionunit"]["dataset"]["samples"][0]["datum"].append(_datum("Pinus", 1)), {},
     "repeated_label"),
    (lambda d: d["data"][1]["site"]["collectionunit"]["dataset"]["samples"][0]["datum"].append(_datum("Pinus", 1, taxonid=7)),
     {}, "label_collision"),
    (lambda d: d["data"][1]["site"]["collectionunit"]["dataset"]["samples"][0]["datum"].append(
        _datum("Pinus", 1, elementtype="stomate")), {}, "label_collision"),
    (lambda d: d["data"][0]["site"]["collectionunit"]["dataset"]["samples"][1]["datum"][0].update(value=2.5), {},
     "invalid_count"),
    (lambda d: d["data"][0]["site"]["collectionunit"]["dataset"]["samples"][1]["datum"][0].update(value=-1), {},
     "invalid_count"),
    (lambda d: d["data"][2]["site"]["collectionunit"]["dataset"]["samples"][0]["datum"][0].update(value=-1.0),
     {"datasets": [3], "units": "percent"}, "invalid_abundance"),
    (lambda d: d["data"][0]["site"]["collectionunit"]["dataset"]["samples"][1].update(depth=20), {"row_order": "depth"},
     "depth_order"),
    (lambda d: d["data"][0]["site"]["collectionunit"]["dataset"]["samples"][1].update(depth=None), {"row_order": "depth"},
     "depth_order"),
    (lambda d: d["data"][0]["site"]["collectionunit"]["dataset"]["samples"][1]["ages"].append(
        {"chronologyid": 10, "age": 1}), {}, "duplicate_age"),
    (lambda d: None, {"ecological_groups": ["AQVP"]}, "empty_selection"),
    (lambda d: d["data"][0]["site"]["collectionunit"]["dataset"]["samples"][0].pop("ages"), {}, "invalid_source"),
    (lambda d: d["data"][0]["site"]["collectionunit"]["dataset"]["samples"][0]["datum"][0].pop("units"), {},
     "invalid_source"),
    (lambda d: d["data"][0]["site"].pop("collectionunit"), {}, "invalid_source"),
])
def test_refusals(tmp_path, change, specchanges, code):
    with pytest.raises(AnalysisError) as error:
        _extract(tmp_path, _mutate(change), **specchanges)
    assert error.value.code == code


def test_source_hash_refusal(tmp_path):
    path, digest = _write(tmp_path, _download())
    with pytest.raises(AnalysisError) as error:
        neotoma_extract(_spec(path, "0" * 64), tmp_path / "out")
    assert error.value.code == "source_hash"


def test_inspection_and_reproduction_survive_moving_the_source(tmp_path):
    out = _extract(tmp_path)
    (tmp_path / "download.json").unlink()
    assert inspect_neotoma(out["bundle"])["status"] == "verified"
    again = reproduce_neotoma(out["bundle"], tmp_path / "again")
    assert again["status"] == "reproduced" and again["differences"] == [] and again["environment_identical"]


def _rehash(bundle, name):
    manifest_path = bundle / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    data = (bundle / name).read_bytes()
    manifest["files"][name] = {"sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data)}
    manifest_path.write_text(json.dumps(manifest, indent=2))


@pytest.mark.parametrize("name,tamper,reason", [
    ("source.json", lambda t: t.replace('"value": 5', '"value": 6'), "source_hash"),
    ("spec.json", lambda t: t.replace('"UPHE"', '"VACR"'), "differ"),
    ("table.tsv", lambda t: t.replace("12\t5\t3", "12\t5\t4"), "table.tsv"),
    ("extract.json", lambda t: t.replace('"data_kept": 4', '"data_kept": 5'), "extract.json"),
])
def test_rehashed_tampering_fails_inspection(tmp_path, name, tamper, reason):
    bundle = Path(_extract(tmp_path)["bundle"])
    path = bundle / name
    original = path.read_text()
    changed = tamper(original)
    assert changed != original
    path.write_text(changed)
    _rehash(bundle, name)
    with pytest.raises(AnalysisError) as error:
        inspect_neotoma(bundle)
    assert reason in str(error.value.details)


def test_cli_extract_resolves_source_beside_the_spec(tmp_path, capsys):
    path, digest = _write(tmp_path, _download())
    spec = _spec("download.json", digest)
    (tmp_path / "spec.json").write_text(json.dumps(spec))
    assert cli_main(["neotoma-extract", str(tmp_path / "spec.json"), "--output", str(tmp_path / "out")]) == 0
    bundle = json.loads(capsys.readouterr().out)["bundle"]
    assert cli_main(["neotoma-inspect", bundle]) == 0
    assert json.loads(capsys.readouterr().out)["status"] == "verified"


def _table(path):
    lines = Path(path).read_text().splitlines()
    header = lines[0].split("\t")[1:]
    return {line.split("\t")[0]: dict(zip(header, line.split("\t")[1:])) for line in lines[1:]}, header


def test_surface_download_matches_the_application_table_by_identity(tmp_path):
    digest = hashlib.sha256(SURFACE.read_bytes()).hexdigest()
    spec = {"source": str(SURFACE), "source_sha256": digest, "datasets": SURFACE_IDS, "units": "percent",
            "elements": ["pollen", "pollen/spore", "spore"], "ecological_groups": ["TRSH", "UPHE"],
            "absent_taxa": "zero", "row_order": "source"}
    out = neotoma_extract(spec, tmp_path)
    assert (out["n_samples"], out["n_labels"]) == (61, 92)
    assert len(_rows(Path(out["bundle"]) / "ages.csv")) == 61
    with pytest.raises(AnalysisError) as error:
        neotoma_extract(dict(spec, datasets="all"), tmp_path)
    assert error.value.code == "mixed_units"


def test_selina_download_reproduces_the_count_table_and_ages(tmp_path):
    digest = hashlib.sha256(SELINA.read_bytes()).hexdigest()
    out = neotoma_extract({"source": str(SELINA), "source_sha256": digest, "datasets": "all", "units": "NISP",
                           "elements": ["pollen"], "ecological_groups": ["TRSH", "UPHE"], "absent_taxa": "zero",
                           "row_order": "depth"}, tmp_path)
    bundle = Path(out["bundle"])
    assert (bundle / "table.tsv").read_bytes() == (ROOT / "analyses/lake-selina/data/counts.tsv").read_bytes()
    ages = _rows(bundle / "ages.csv")
    assert len(ages) == 144 and sum(a["is_default_chronology"] == "true" for a in ages) == 72
    by = {(a["sample_id"], a["chronologyid"]): a["age"] for a in ages}
    levels = _rows(ROOT / "analyses/lake-selina/data/levels.csv")
    assert all(by[(lv["sample_id"], "37590")] == lv["age_ippd2"] and by[(lv["sample_id"], "37589")] == lv["age_ippd1"]
               for lv in levels)
    assert {row["geometry_type"] for row in _rows(bundle / "samples.csv")} == {"Polygon"}
