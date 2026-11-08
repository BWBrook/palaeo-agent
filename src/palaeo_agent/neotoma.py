"""Deterministic intake of a saved Neotoma `data/downloads` file into a portable extraction bundle."""

import csv
import io
import json
import math
from pathlib import Path, PurePosixPath
import uuid
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator

from .core import AnalysisError
from .runs import RunEnvironment, _environment, _find_lockfile, _json, _sha

EXTRACTOR_VERSION = 1
DERIVED = ("table.tsv", "samples.csv", "ages.csv", "taxa.csv", "extract.json")
BUNDLE_FILES = {"source.json", "spec.json", *DERIVED, "environment.json"}
SAMPLE_COLUMNS = ["sample_id", "datasetid", "datasetname", "doi", "siteid", "sitename", "collectionunitid", "handle",
                  "collunittype", "depositionalenvironment", "depth", "thickness", "samplename", "analysisunitname",
                  "geometry_type", "lon", "lat", "site_altitude", "collectionunit_notes", "sample_notes", "dataset_pi",
                  "shares_coordinates_with"]
AGE_COLUMNS = ["sample_id", "chronologyid", "chronologyname", "agetype", "age", "ageolder", "ageyounger",
               "is_default_chronology"]
TAXON_KEYS = ("taxonid", "element", "elementtype", "ecologicalgroup", "taxongroup")
TAXA_COLUMNS = ["label", "taxonid", "taxongroup", "ecologicalgroup", "element", "elementtype", "units",
                "n_samples_positive"]
SCOPE = ("Deterministic intake only: units, filters and zero-fill are declared; sample selection, overrides, "
         "harmonisation, closure, imputation and chronology choice remain with the caller")


class NeotomaSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")
    source: Path
    source_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    datasets: Literal["all"] | list[int] = Field(description="'all' or explicit dataset IDs; units validate, never filter")
    units: Literal["NISP", "percent"] = Field(description="NISP gives table kind counts; percent gives abundance")
    elements: list[str] = Field(min_length=1)
    ecological_groups: list[str] = Field(min_length=1)
    absent_taxa: Literal["zero"] = Field(description="Declares that a taxon absent from a sample's kept data is zero")
    row_order: Literal["source", "depth"]

    @field_validator("datasets", "elements", "ecological_groups")
    @classmethod
    def unique(cls, value):
        if isinstance(value, list) and (not value or len(set(value)) != len(value)):
            raise ValueError("Lists must be non-empty and free of repeats")
        return value


def _require(container, key, kind, where):
    if not isinstance(container, dict) or key not in container or not isinstance(container[key], kind) \
            or isinstance(container[key], bool):
        raise AnalysisError("invalid_source", "Saved download lacks a required key or has the wrong type",
                            key=key, where=where)
    return container[key]


def _cell(value):
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, (bool, list, dict)):
        return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return repr(value)


def _csv(header, rows):
    stream = io.StringIO()
    writer = csv.writer(stream, lineterminator="\n")
    writer.writerow(header)
    writer.writerows(rows)
    return stream.getvalue().encode("utf-8")


def _geometry(site):
    raw = site.get("geography")
    if not isinstance(raw, str):
        return "", "", ""
    try:
        geometry = json.loads(raw)
    except json.JSONDecodeError:
        return "", "", ""
    kind = geometry.get("type") if isinstance(geometry, dict) else None
    coordinates = geometry.get("coordinates") if isinstance(geometry, dict) else None
    if kind == "Point" and isinstance(coordinates, list) and len(coordinates) >= 2:
        return kind, _cell(coordinates[0]), _cell(coordinates[1])
    return _cell(kind), "", ""


def _value(datum, units, sample_id, label):
    value = datum["value"]
    if units == "NISP":
        if type(value) is not int or value < 0:
            raise AnalysisError("invalid_count", "NISP values must be integers of at least zero",
                                sample_id=sample_id, label=label)
    elif isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0:
        raise AnalysisError("invalid_abundance", "Percent values must be finite and nonnegative",
                            sample_id=sample_id, label=label)
    return value


def extract(spec, source_bytes):
    """Derive the five deterministic outputs from source bytes; no file system access."""
    spec = spec if isinstance(spec, NeotomaSpec) else NeotomaSpec.model_validate(spec)
    if _sha(source_bytes) != spec.source_sha256:
        raise AnalysisError("source_hash", "Source bytes do not match the declared SHA-256",
                            declared=spec.source_sha256, actual=_sha(source_bytes))
    try:
        document = json.loads(source_bytes.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise AnalysisError("invalid_source", "Saved download is not UTF-8 JSON") from exc
    records = _require(document, "data", list, "top")
    datasets, seen_ids = [], set()
    for index, record in enumerate(records):
        site = _require(record, "site", dict, f"data[{index}]")
        for key, kind in (("siteid", int), ("sitename", str)):
            _require(site, key, kind, f"data[{index}].site")
        unit = _require(site, "collectionunit", dict, f"data[{index}].site")
        _require(unit, "collectionunitid", int, f"data[{index}].collectionunit")
        dataset = _require(unit, "dataset", dict, f"data[{index}].collectionunit")
        dataset_id = _require(dataset, "datasetid", int, f"data[{index}].dataset")
        _require(dataset, "samples", list, f"dataset {dataset_id}")
        if dataset_id in seen_ids:
            raise AnalysisError("duplicate_dataset", "A dataset ID appears twice in the download", datasetid=dataset_id)
        seen_ids.add(dataset_id)
        datasets.append((site, unit, dataset))
    if spec.datasets != "all":
        unknown = sorted(set(spec.datasets) - seen_ids)
        if unknown:
            raise AnalysisError("unknown_dataset", "Declared datasets are absent from the download", datasets=unknown)
        wanted = set(spec.datasets)
        datasets = [item for item in datasets if item[2]["datasetid"] in wanted]

    rows, sample_ids, taxa, dropped = [], set(), {}, {}
    data_seen = data_kept = 0
    elements, groups = set(spec.elements), set(spec.ecological_groups)
    for site, unit, dataset in datasets:
        samples = []
        for sample in dataset["samples"]:
            where = f"dataset {dataset['datasetid']}"
            sample_id = str(_require(sample, "sampleid", int, where))
            _require(sample, "datum", list, f"sample {sample_id}")
            _require(sample, "ages", list, f"sample {sample_id}")
            if sample_id in sample_ids:
                raise AnalysisError("duplicate_sample", "A sample ID repeats", sample_id=sample_id)
            sample_ids.add(sample_id)
            values = {}
            for datum in sample["datum"]:
                label = _require(datum, "variablename", str, f"sample {sample_id}")
                if not label:
                    raise AnalysisError("invalid_source", "Empty variablename", where=f"sample {sample_id}")
                for key in ("value", "units", "element", "ecologicalgroup", "taxonid"):
                    if key not in datum:
                        raise AnalysisError("invalid_source", "Datum lacks a required key", key=key,
                                            where=f"sample {sample_id}")
                data_seen += 1
                if datum["element"] not in elements or datum["ecologicalgroup"] not in groups:
                    key = (str(datum["element"]), str(datum["ecologicalgroup"]), str(datum["units"]))
                    dropped[key] = dropped.get(key, 0) + 1
                    continue
                if datum["units"] != spec.units:
                    raise AnalysisError("mixed_units", "A kept datum has other units than declared",
                                        declared=spec.units, found=datum["units"], sample_id=sample_id,
                                        datasetid=dataset["datasetid"], label=label)
                if label in values:
                    raise AnalysisError("repeated_label", "One sample has two kept data with the same label",
                                        sample_id=sample_id, label=label)
                identity = tuple(datum.get(key) for key in TAXON_KEYS)
                if taxa.setdefault(label, identity) != identity:
                    raise AnalysisError("label_collision", "One label maps to more than one taxon identity",
                                        label=label, identities=[list(taxa[label]), list(identity)])
                values[label] = _value(datum, spec.units, sample_id, label)
                data_kept += 1
            samples.append((sample, values))
        if spec.row_order == "depth":
            depths = [s.get("depth") for s, _ in samples]
            if any(isinstance(d, bool) or not isinstance(d, (int, float)) for d in depths) or len(set(depths)) != len(depths):
                raise AnalysisError("depth_order", "Depth ordering needs a distinct numeric depth for every sample",
                                    datasetid=dataset["datasetid"])
            samples.sort(key=lambda item: item[0]["depth"])
        rows.extend((site, unit, dataset, sample, values) for sample, values in samples)
    if not data_kept:
        raise AnalysisError("empty_selection", "No kept datum remains after the declared filters")

    labels = sorted(taxa)
    table = ["\t".join(["sample_id", *labels])]
    table += ["\t".join([str(sample["sampleid"]), *[repr(values[n]) if n in values else "0" for n in labels]])
              for _, _, _, sample, values in rows]

    points = {}
    for site, _, _, _, _ in rows:
        kind, lon, lat = _geometry(site)
        if kind == "Point":
            points.setdefault((lon, lat), set()).add(site["sitename"])
    sample_rows, age_rows, age_keys = [], [], set()
    for site, unit, dataset, sample, values in rows:
        kind, lon, lat = _geometry(site)
        sample_id = str(sample["sampleid"])
        shared = sorted(points.get((lon, lat), set()) - {site["sitename"]}) if kind == "Point" else []
        sample_rows.append([sample_id, *[_cell(v) for v in (
            dataset["datasetid"], dataset.get("datasetname"), dataset.get("doi"), site["siteid"], site["sitename"],
            unit["collectionunitid"], unit.get("handle"), unit.get("collunittype"), unit.get("depositionalenvironment"),
            sample.get("depth"), sample.get("thickness"), sample.get("samplename"), sample.get("analysisunitname"))],
            kind, lon, lat, *[_cell(v) for v in (site.get("altitude"), unit.get("notes"), sample.get("samplenotes"),
                                                 dataset.get("datasetpi"))], "; ".join(shared)])
        default = unit.get("defaultchronology")
        for age in sample["ages"]:
            chronology = _require(age, "chronologyid", int, f"sample {sample_id} ages")
            if (sample_id, chronology) in age_keys:
                raise AnalysisError("duplicate_age", "A sample has two ages for one chronology",
                                    sample_id=sample_id, chronologyid=chronology)
            age_keys.add((sample_id, chronology))
            age_rows.append([sample_id, str(chronology), *[_cell(age.get(k)) for k in
                             ("chronologyname", "agetype", "age", "ageolder", "ageyounger")],
                             "true" if default is not None and chronology == default else "false"])
    positive = {n: sum(1 for *_, values in rows if values.get(n, 0) > 0) for n in labels}
    taxa_rows = [[n, *[_cell(dict(zip(TAXON_KEYS, taxa[n]))[k]) for k in TAXA_COLUMNS[1:6]], spec.units, positive[n]]
                 for n in labels]
    all_zero = [str(sample["sampleid"]) for _, _, _, sample, values in rows if not any(v > 0 for v in values.values())]
    record = {
        "extractor": "neotoma_extract", "extractor_version": EXTRACTOR_VERSION,
        "specification": spec.model_copy(update={"source": Path("source.json")}).model_dump(mode="json"),
        "source_sha256": spec.source_sha256,
        "kind": "counts" if spec.units == "NISP" else "abundance",
        "datasets_in_source": len(records), "datasets_selected": [d["datasetid"] for _, _, d in datasets],
        "n_samples": len(rows), "n_labels": len(labels), "n_age_rows": len(age_rows),
        "data_seen": data_seen, "data_kept": data_kept,
        "dropped": [{"element": e, "ecologicalgroup": g, "units": u, "n": n} for (e, g, u), n in sorted(dropped.items())],
        "all_zero_samples": all_zero, "scope": SCOPE,
    }
    return {
        "table.tsv": ("\n".join(table) + "\n").encode("utf-8"),
        "samples.csv": _csv(SAMPLE_COLUMNS, sample_rows),
        "ages.csv": _csv(AGE_COLUMNS, age_rows),
        "taxa.csv": _csv(TAXA_COLUMNS, taxa_rows),
        "extract.json": (json.dumps(record, indent=2, allow_nan=False) + "\n").encode("utf-8"),
    }


def neotoma_extract(spec, output_root: str | Path):
    """Extract a saved download into a new self-contained bundle under output_root."""
    try:
        spec = spec if isinstance(spec, NeotomaSpec) else NeotomaSpec.model_validate(spec)
    except ValidationError as exc:
        raise AnalysisError("invalid_specification", "Request does not match the neotoma_extract schema",
                            details=json.loads(exc.json(include_url=False, include_context=False))) from exc
    source_bytes = Path(spec.source).read_bytes()
    derived = extract(spec, source_bytes)
    directory = Path(output_root).resolve() / uuid.uuid4().hex
    directory.mkdir(parents=True, exist_ok=False)
    (directory / "source.json").write_bytes(source_bytes)
    _json(directory / "spec.json", spec.model_copy(update={"source": Path("source.json")}).model_dump(mode="json"))
    for name, data in derived.items():
        (directory / name).write_bytes(data)
    _json(directory / "environment.json", _environment(_find_lockfile()))
    files = {path.name: {"sha256": _sha(path.read_bytes()), "bytes": path.stat().st_size}
             for path in sorted(directory.iterdir())}
    _json(directory / "manifest.json", {"schema_version": 1, "kind": "neotoma_extraction", "files": files})
    record = json.loads(derived["extract.json"])
    return {"status": "complete", "bundle": str(directory), "table": str(directory / "table.tsv"),
            "samples": str(directory / "samples.csv"), "kind": record["kind"], "n_samples": record["n_samples"],
            "n_labels": record["n_labels"], "all_zero_samples": record["all_zero_samples"], "scope": SCOPE}


def inspect_neotoma(bundle: str | Path):
    """Verify an extraction bundle from its own snapshot: hashes, then byte-for-byte re-derivation."""
    directory = Path(bundle).resolve()
    try:
        manifest = json.loads((directory / "manifest.json").read_text(encoding="utf-8"))
        if manifest.get("schema_version") != 1 or manifest.get("kind") != "neotoma_extraction":
            raise ValueError("Not a schema-1 Neotoma extraction bundle")
        if set(manifest["files"]) != BUNDLE_FILES:
            raise ValueError("Manifest file set differs from the extraction layout")
        if {item.name for item in directory.iterdir()} != BUNDLE_FILES | {"manifest.json"}:
            raise ValueError("Bundle file set differs from manifest")
        for name, expected in manifest["files"].items():
            path = directory / name
            if len(PurePosixPath(name).parts) != 1 or path.is_symlink() or not path.is_file():
                raise ValueError("Unsafe artefact path")
            data = path.read_bytes()
            if _sha(data) != expected["sha256"] or len(data) != expected["bytes"]:
                raise ValueError(f"Artefact integrity failure: {name}")
        spec = NeotomaSpec.model_validate_json((directory / "spec.json").read_bytes())
        if spec.source != Path("source.json"):
            raise ValueError("Saved specification must reference its source snapshot")
        derived = extract(spec, (directory / "source.json").read_bytes())
        changed = [name for name in DERIVED if derived[name] != (directory / name).read_bytes()]
        if changed:
            raise ValueError(f"Derived files differ from re-extraction: {', '.join(changed)}")
        environment = RunEnvironment.model_validate_json((directory / "environment.json").read_bytes())
    except AnalysisError as exc:
        raise AnalysisError("invalid_bundle", "Extraction failed re-derivation", bundle=str(directory),
                            reason=str(exc), extraction_error=exc.code) from exc
    except (OSError, ValueError, KeyError, TypeError) as exc:
        raise AnalysisError("invalid_bundle", "Extraction bundle could not be verified", bundle=str(directory),
                            reason=str(exc)) from exc
    return {"status": "verified", "bundle": str(directory), "extract": json.loads(derived["extract.json"]),
            "specification": spec.model_dump(mode="json"),
            "environment": environment.model_dump(mode="json"),
            "scope": "Integrity and byte-for-byte re-derivation from the bundled source verified; " + SCOPE}


def reproduce_neotoma(bundle: str | Path, output_root: str | Path):
    original = inspect_neotoma(bundle)
    directory = Path(original["bundle"])
    spec = NeotomaSpec.model_validate(original["specification"]).model_copy(update={"source": directory / "source.json"})
    fresh = neotoma_extract(spec, output_root)
    recreated = inspect_neotoma(fresh["bundle"])
    new = Path(fresh["bundle"])
    differences = [name for name in DERIVED if (directory / name).read_bytes() != (new / name).read_bytes()]
    return {"status": "reproduced" if not differences else "different", "original": str(directory),
            "new": str(new), "differences": differences,
            "environment_identical": original["environment"] == recreated["environment"],
            "scope": "Derived files compared byte for byte; environment provenance reported separately"}
