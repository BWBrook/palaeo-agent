"""Reproducible multi-step studies: declared preparation composed with saved runs.

A study names raw inputs, derives datasets from them through a closed set of
explicit operations, runs supported analyses on those datasets and saves one
bundle whose every step can be inspected and recomputed. Nothing is inferred:
no label merges, missing-value replacement or sampling assumption happens
unless the study declares it.
"""

import csv
from decimal import Decimal, Inexact, InvalidOperation, localcontext
import hashlib
import io
import json
import os
import shutil
from pathlib import Path, PurePosixPath
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator

from .community import FORMAT_HELP, check_delimiter, parse_table
from .core import AnalysisError, decimal_context, resolve_columns
from .methods import parse_spec, summary
from .runs import inspect_run, require_outside, run

STUDY_VERSION = 1
MANIFEST_KEYS = {"study_version", "status", "steps", "runs", "row_filter_warnings", "files"}
# IDs become path components (inputs/<id>, derived/<id>.dat, runs/<id>), so none may start with a dot.
ID = Annotated[str, Field(min_length=1, pattern=r"^[A-Za-z0-9_-][A-Za-z0-9_.-]*$")]


class Model(BaseModel):
    model_config = ConfigDict(extra="forbid")


class TableInput(Model):
    kind: Literal["counts", "abundance", "measurements"] = Field(
        description="counts: exact integer specimen counts; abundance: fractional weights (percentages, proportions); "
                    "measurements: continuous variables for rma")
    path: Path = Field(description="Table path, relative to the study file")
    format: Literal["past", "delimited"] = Field(default="past", description=FORMAT_HELP)
    delimiter: Literal["tab", "comma"] | None = Field(default=None, description="Required for format 'delimited'")

    @model_validator(mode="after")
    def declared_delimiter(self):
        check_delimiter(self)
        return self

    orientation: Literal["samples_by_taxa", "taxa_by_samples"] = Field(
        description="Declared layout; derived datasets are always samples_by_taxa")


class MetadataInput(Model):
    kind: Literal["metadata"]
    path: Path = Field(description="UTF-8 CSV; relative to the study file")
    id_column: str = Field(min_length=1, description="Exact column holding sample IDs")


class Exclude(Model):
    op: Literal["exclude"]
    samples: list[str] = Field(min_length=1)
    reason: str = Field(min_length=1, pattern=r"\S")


class Select(Model):
    op: Literal["select"]
    samples: list[str] = Field(min_length=1, description="Samples kept, in this order")
    reason: str = Field(min_length=1, pattern=r"\S")


class MapTaxa(Model):
    op: Literal["map_taxa"]
    mapping: dict[str, str] = Field(min_length=1, description="Exact old label -> new label; equal targets are summed")
    reason: str = Field(min_length=1, pattern=r"\S")


class ExcludeTaxa(Model):
    op: Literal["exclude_taxa"]
    taxa: list[str] = Field(min_length=1, description="Exact count-column labels removed; retained order is kept")
    reason: str = Field(min_length=1, pattern=r"\S")


Operation = Annotated[Exclude | Select | MapTaxa | ExcludeTaxa, Field(discriminator="op")]


class Dataset(Model):
    source: ID
    metadata: ID | None = None
    drop_unmatched_metadata: bool = Field(
        default=False, description="Allow metadata rows whose IDs are absent from the dataset; they are listed")
    operations: list[Operation] = []


class Analysis(Model):
    id: ID
    dataset: ID
    spec: dict = Field(description="A method specification without input or metadata paths")


class StudySpec(Model):
    study_version: Literal[1]
    inputs: dict[ID, Annotated[TableInput | MetadataInput, Field(discriminator="kind")]]
    datasets: dict[ID, Dataset]
    analyses: list[Analysis] = Field(min_length=1)

    @model_validator(mode="after")
    def references(self):
        for name, dataset in self.datasets.items():
            if not isinstance(self.inputs.get(dataset.source), TableInput):
                raise ValueError(f"Dataset {name} must name a table input as its source")
            if dataset.metadata is not None and not isinstance(self.inputs.get(dataset.metadata), MetadataInput):
                raise ValueError(f"Dataset {name} must name a metadata input")
            if dataset.drop_unmatched_metadata and dataset.metadata is None:
                raise ValueError(f"Dataset {name} cannot drop metadata it does not have")
        ids = [analysis.id for analysis in self.analyses]
        if len(ids) != len(set(ids)):
            raise ValueError("Analysis IDs must be unique")
        for analysis in self.analyses:
            if analysis.dataset not in self.datasets:
                raise ValueError(f"Analysis {analysis.id} names an unknown dataset")
            if {"input", "metadata"} & set(analysis.spec):
                raise ValueError(f"Analysis {analysis.id}: the study supplies input and metadata paths")
            kind = self.inputs[self.datasets[analysis.dataset].source].kind
            method = analysis.spec.get("method")
            if (method == "rma") != (kind == "measurements"):
                raise ValueError(f"Analysis {analysis.id}: {method} cannot analyse a {kind} dataset")
            if kind == "abundance" and method not in ("community", "permanova"):
                raise ValueError(f"Analysis {analysis.id}: {method} requires counts; abundance weights are never converted")
            if kind != "measurements" and analysis.spec.get("value_type") != ("abundance" if kind == "abundance" else "count"):
                raise ValueError(f"Analysis {analysis.id}: value_type must match the {kind} input declaration")
            if analysis.spec.get("format") != "past" or analysis.spec.get("orientation", "samples_by_taxa") != "samples_by_taxa":
                raise ValueError(f"Analysis {analysis.id}: derived datasets are PAST tables, samples by taxa")
        return self

    def step_ids(self):
        return [f"dataset:{name}" for name in self.datasets] + [f"analysis:{a.id}" for a in self.analyses]


def _sha(data):
    return hashlib.sha256(data).hexdigest()


def _unique(labels, role):
    seen, repeated = set(), set()
    for label in labels:
        (repeated if label in seen else seen).add(label)
    if repeated:
        raise AnalysisError("duplicate_id", "IDs must be unique", role=role, ids=sorted(repeated))


def read_table(data: bytes, declaration: TableInput):
    try:
        text = data.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise AnalysisError("invalid_encoding", "Tables must be UTF-8 text") from exc
    rows = parse_table(text, declaration.format, declaration.delimiter)
    columns, labels = rows[0][1:], [row[0] for row in rows[1:]]
    for line, row in enumerate(rows[1:], 2):
        if len(row) != len(columns) + 1:
            raise AnalysisError("row_width", "Row width differs from the header", line=line)
    values = [row[1:] for row in rows[1:]]
    if declaration.orientation == "taxa_by_samples":
        values = [list(column) for column in zip(*values)]
        labels, columns = columns, labels
    _unique(labels, "sample")
    _unique(columns, "column")
    return {"samples": labels, "columns": columns, "values": values}


def read_metadata(data: bytes, declaration: MetadataInput):
    try:
        material = list(csv.reader(io.StringIO(data.decode("utf-8-sig"))))
    except (UnicodeDecodeError, csv.Error) as exc:
        raise AnalysisError("invalid_metadata", "Metadata must be UTF-8 CSV") from exc
    if not material or declaration.id_column not in material[0]:
        raise AnalysisError("invalid_metadata", "Metadata lacks the declared ID column", id_column=declaration.id_column)
    header = material[0]
    _unique(header, "metadata_column")
    if declaration.id_column != "sample_id" and "sample_id" in header:
        raise AnalysisError("ambiguous_metadata_id", "A separate sample_id column would be shadowed by the declared ID column")
    if any(len(row) != len(header) for row in material[1:]):
        raise AnalysisError("invalid_metadata", "Metadata row width differs from its header")
    rows = [dict(zip(header, row)) for row in material[1:]]
    _unique([row[declaration.id_column] for row in rows], "metadata_sample")
    order = [declaration.id_column] + [name for name in header if name != declaration.id_column]
    return {"header": ["sample_id"] + order[1:],
            "rows": {row[declaration.id_column]: [row[name] for name in order] for row in rows}}


def _integer(token, sample, column):
    try:
        value = Decimal(token)
    except InvalidOperation as exc:
        raise AnalysisError("invalid_count", "Merged cells must be exact counts", sample=sample, column=column) from exc
    if not value.is_finite() or value < 0 or value != value.to_integral_value():
        raise AnalysisError("invalid_count", "Merged cells must be exact nonnegative integers", sample=sample, column=column)
    return int(value)


def _weight_sum(tokens, sample, columns):
    """Exact decimal sum of abundance weights; refuses rather than rounds."""
    with localcontext(decimal_context(1000, Inexact)):
        try:
            values = [Decimal(token) for token in tokens]
            if any(not value.is_finite() or value < 0 for value in values):
                raise InvalidOperation
            total = sum(values, Decimal(0))
        except (InvalidOperation, Inexact) as exc:
            raise AnalysisError("invalid_abundance", "Merged abundance cells must be finite nonnegative decimals",
                                sample=sample, columns=columns) from exc
    return format(total, "f")


def _is_zero(cell):
    try:
        return Decimal(cell) == 0
    except InvalidOperation:
        return False


def apply(operation, table, kind):
    """Apply one declared operation; return the new table and its record."""
    samples, columns, values = table["samples"], table["columns"], table["values"]
    if operation.op in ("exclude", "select"):
        unknown = sorted(set(operation.samples) - set(samples))
        if unknown:
            raise AnalysisError("unknown_sample", "Declared samples do not exist", samples=unknown)
        _unique(operation.samples, "declared_sample")
        if operation.op == "exclude":
            keep = [s for s in samples if s not in set(operation.samples)]
        else:
            keep = list(operation.samples)
        if not keep:
            raise AnalysisError("no_samples", "The operation removes every sample")
        index = {s: i for i, s in enumerate(samples)}
        record = {"op": operation.op, "reason": operation.reason, "kept": keep,
                  "removed": [s for s in samples if s not in set(keep)]}
        return {"samples": keep, "columns": columns, "values": [values[index[s]] for s in keep]}, record
    if kind == "measurements":
        raise AnalysisError("operation_not_applicable", "Taxon operations apply only to count or abundance tables")
    if operation.op == "exclude_taxa":
        unknown = sorted(set(operation.taxa) - set(columns))
        if unknown:
            raise AnalysisError("unknown_taxon", "Excluded labels do not exist", labels=unknown)
        _unique(operation.taxa, "declared_taxon")
        keep = [i for i, c in enumerate(columns) if c not in set(operation.taxa)]
        if not keep:
            raise AnalysisError("no_taxa", "The operation removes every taxon")
        new_values = [[row[i] for i in keep] for row in values]
        emptied = [s for s, row in zip(samples, new_values) if all(_is_zero(cell) for cell in row)]
        record = {"op": "exclude_taxa", "reason": operation.reason, "removed": list(operation.taxa),
                  "columns": [columns[i] for i in keep], "emptied_samples": emptied}
        return {"samples": samples, "columns": [columns[i] for i in keep], "values": new_values}, record
    unknown = sorted(set(operation.mapping) - set(columns))
    if unknown:
        raise AnalysisError("unknown_taxon", "Mapped labels do not exist", labels=unknown)
    targets = [operation.mapping.get(c, c) for c in columns]
    order = list(dict.fromkeys(targets))
    merged = {t: [c for c, target in zip(columns, targets) if target == t] for t in order}
    new_values = []
    for sample, row in zip(samples, values):
        cells = dict(zip(columns, row))
        new_row = []
        for target in order:
            sources = merged[target]
            if len(sources) == 1:
                new_row.append(cells[sources[0]])
            elif any(cells[c] == "." for c in sources):
                raise AnalysisError("missing_counts", "Missing cells cannot be merged", sample=sample, columns=sources)
            elif kind == "counts":
                new_row.append(str(sum(_integer(cells[c], sample, c) for c in sources)))
            else:
                new_row.append(_weight_sum([cells[c] for c in sources], sample, sources))
        new_values.append(new_row)
    record = {"op": "map_taxa", "reason": operation.reason, "mapping": operation.mapping,
              "merged": {t: s for t, s in merged.items() if len(s) > 1}, "columns": order}
    return {"samples": samples, "columns": order, "values": new_values}, record


ROW_FILTER_MESSAGE = ("A row filter removed complete x/y pairs from this analysis's columns. Confirm that this "
                      "exclusion applies to this analysis; the warning does not judge whether it is right.")


def _present(cell):
    return cell.strip() not in ("", ".")


def row_filter_warnings(spec: StudySpec, raw: dict, datasets=None):
    """For each rma analysis, report row filters that remove complete pairs in its x/y columns.

    Each operation's removals are counted from its incoming table, so sequential filters never
    double-count. Recomputed from saved inputs during inspection."""
    warnings = []
    for analysis in spec.analyses:
        if analysis.spec.get("method") != "rma" or (datasets is not None and analysis.dataset not in datasets):
            continue
        dataset = spec.datasets[analysis.dataset]
        declaration = spec.inputs[dataset.source]
        x, y = analysis.spec.get("x"), analysis.spec.get("y")
        table = read_table(raw[dataset.source], declaration)
        for index, operation in enumerate(dataset.operations):
            incoming = table
            table, record = apply(operation, table, declaration.kind)
            if operation.op not in ("exclude", "select"):
                continue
            try:
                i, j = resolve_columns(incoming["columns"], x, y)
            except AnalysisError:
                continue
            rows = dict(zip(incoming["samples"], incoming["values"]))
            removed = [s for s in record["removed"] if _present(rows[s][i]) and _present(rows[s][j])]
            if removed:
                warnings.append({"code": "row_filter_removes_pairs", "message": ROW_FILTER_MESSAGE,
                                 "analysis": analysis.id, "dataset": analysis.dataset, "x": x, "y": y,
                                 "operation_index": index, "op": operation.op, "removed_rows": removed,
                                 "complete_pairs_removed": len(removed), "reason": operation.reason})
    return warnings


def _past(table):
    lines = ["\t".join([".", *table["columns"]])]
    lines += ["\t".join([sample, *row]) for sample, row in zip(table["samples"], table["values"])]
    return ("\n".join(lines) + "\n").encode()


def _csv(header, rows):
    stream = io.StringIO()
    writer = csv.writer(stream, lineterminator="\n")
    writer.writerow(header)
    writer.writerows(rows)
    return stream.getvalue().encode()


def derive(spec: StudySpec, raw: dict, name: str):
    """Derive one dataset from raw input bytes. Pure: identical inputs give identical bytes."""
    dataset = spec.datasets[name]
    declaration = spec.inputs[dataset.source]
    table = read_table(raw[dataset.source], declaration)
    records = [{"op": "read", "input": dataset.source, "orientation": declaration.orientation,
                "samples": len(table["samples"]), "columns": len(table["columns"])}]
    for operation in dataset.operations:
        table, record = apply(operation, table, declaration.kind)
        records.append(record)
    files = {f"{name}.dat": _past(table)}
    if parse_table(files[f"{name}.dat"].decode(), "past") != [[".", *table["columns"]]] + [
            [sample, *row] for sample, row in zip(table["samples"], table["values"])]:
        raise AnalysisError("unsupported_label", "A sample or column label cannot be written to a PAST table "
                            "(it contains a tab or line break)", dataset=name)
    if dataset.metadata is not None:
        metadata = read_metadata(raw[dataset.metadata], spec.inputs[dataset.metadata])
        missing = [s for s in table["samples"] if s not in metadata["rows"]]
        if missing:
            raise AnalysisError("metadata_alignment", "Dataset samples lack metadata rows", missing=missing)
        unmatched = [s for s in metadata["rows"] if s not in set(table["samples"])]
        if unmatched and not dataset.drop_unmatched_metadata:
            raise AnalysisError("metadata_alignment", "Metadata rows lack dataset samples; declare drop_unmatched_metadata",
                                unmatched=unmatched)
        records.append({"op": "join_metadata", "input": dataset.metadata, "matched": len(table["samples"]),
                        "dropped_unmatched": unmatched})
        files[f"{name}-metadata.csv"] = _csv(metadata["header"], [metadata["rows"][s] for s in table["samples"]])
    return files, {"dataset": name, "kind": declaration.kind, "samples": table["samples"],
                   "columns": table["columns"], "operations": records}


def _load(study):
    if isinstance(study, (str, Path)):
        path = Path(study).resolve()
        return StudySpec.model_validate_json(path.read_bytes()), path.parent
    return StudySpec.model_validate(study), None


def _write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


def _json(value):
    return (json.dumps(value, indent=2, allow_nan=False) + "\n").encode()


def run_study(study, output_root, *, base_dir=None):
    """Run a study and save its bundle. A failed step is recorded and stops later steps."""
    try:
        spec, file_base = _load(study)
    except ValidationError as exc:
        raise AnalysisError("invalid_study", "Study does not match the schema",
                            details=json.loads(exc.json(include_url=False, include_context=False, include_input=False))) from exc
    base = Path(base_dir or file_base or ".").resolve()
    raw = {}
    for name, declaration in spec.inputs.items():
        path = declaration.path if declaration.path.is_absolute() else base / declaration.path
        try:
            raw[name] = path.read_bytes()
        except OSError as exc:
            raise AnalysisError("input_unreadable", "Cannot read study input", input=name, reason=str(exc)) from exc
    directory = Path(output_root).resolve()
    try:
        directory.mkdir(parents=True, exist_ok=False)
    except FileExistsError as exc:
        raise AnalysisError("output_exists", "The study bundle directory already exists; give a new path for this study",
                            study_dir=str(directory)) from exc
    portable = spec.model_dump(mode="json")
    for name, item in portable["inputs"].items():
        item["path"] = f"inputs/{name}"
        _write(directory / "inputs" / name, raw[name])
    _write(directory / "study.json", _json(portable))
    steps, datasets = [], {}
    for name in spec.datasets:
        if any(step["status"] == "failed" for step in steps):
            steps.append({"id": f"dataset:{name}", "status": "not_run"})
            continue
        try:
            files, record = derive(spec, raw, name)
        except AnalysisError as exc:
            steps.append({"id": f"dataset:{name}", "status": "failed", "error": exc.as_dict()})
            continue
        for filename, data in files.items():
            _write(directory / "derived" / filename, data)
        _write(directory / "derived" / f"{name}.json", _json(record))
        datasets[name] = record
        steps.append({"id": f"dataset:{name}", "status": "complete"})
    runs = {}
    for analysis in spec.analyses:
        if any(step["status"] == "failed" for step in steps):
            steps.append({"id": f"analysis:{analysis.id}", "status": "not_run"})
            continue
        method_spec = dict(analysis.spec, input=str(directory / "derived" / f"{analysis.dataset}.dat"))
        if spec.datasets[analysis.dataset].metadata is not None:
            method_spec["metadata"] = str(directory / "derived" / f"{analysis.dataset}-metadata.csv")
        try:
            outcome = run(parse_spec(method_spec), directory / "runs" / analysis.id)
        except (AnalysisError, ValidationError) as exc:
            # A child bundle that failed while writing is incomplete evidence; its error is kept in the step record.
            shutil.rmtree(directory / "runs" / analysis.id, ignore_errors=True)
            error = exc.as_dict() if isinstance(exc, AnalysisError) else {
                "status": "error", "code": "invalid_specification",
                "details": json.loads(exc.json(include_url=False, include_context=False, include_input=False))}
            steps.append({"id": f"analysis:{analysis.id}", "status": "failed", "error": error})
            continue
        run_dir = Path(outcome["run_dir"])
        runs[analysis.id] = {"run_dir": run_dir.relative_to(directory).as_posix(),
                             "manifest_sha256": _sha((run_dir / "manifest.json").read_bytes())}
        steps.append({"id": f"analysis:{analysis.id}", "status": "complete"})
    status = "complete" if all(step["status"] == "complete" for step in steps) else "partial"
    filters = row_filter_warnings(spec, raw, datasets)
    _write(directory / "report.md", report(spec, datasets, runs, steps, directory, filters).encode())
    files = {path.relative_to(directory).as_posix(): _sha(path.read_bytes())
             for path in sorted(directory.rglob("*")) if path.is_file() and not path.relative_to(directory).parts[0] == "runs"}
    manifest = {"study_version": STUDY_VERSION, "status": status, "steps": steps, "runs": runs,
                "row_filter_warnings": filters, "files": files}
    _write(directory / "manifest.json", _json(manifest))
    failed = next((step for step in steps if step["status"] == "failed"), None)
    return {"status": status, "study_dir": str(directory), "steps": steps, "row_filter_warnings": filters,
            **({"failed_step": failed["id"], "error": failed["error"]} if failed else {})}


def report(spec, datasets, runs, steps, directory, filters):
    lines = ["# Study report", "",
             "Factual record generated from the saved study. Every number links to the field it came from;",
             "scientific interpretation and sampling validity are not established by this report.", ""]
    for step in steps:
        if step["status"] != "complete":
            lines.append(f"- **{step['id']}: {step['status']}**" +
                         (f" — `{step['error'].get('code')}`: {step['error'].get('message')}" if "error" in step else ""))
    for name, record in datasets.items():
        lines += ["", f"## Dataset `{name}`", "",
                  f"{len(record['samples'])} samples × {len(record['columns'])} columns "
                  f"(`derived/{name}.json`)."]
        for operation in record["operations"][1:]:
            if operation["op"] in ("exclude", "select") and operation["removed"]:
                lines.append(f"- {operation['op']}: removed {', '.join(operation['removed'])} — {operation['reason']}")
            elif operation["op"] == "map_taxa":
                merged = "; ".join(f"{t} ← {' + '.join(s)}" for t, s in operation["merged"].items()) or "renames only"
                lines.append(f"- map_taxa: {merged} — {operation['reason']}")
            elif operation["op"] == "exclude_taxa":
                emptied = ", ".join(operation["emptied_samples"]) or "none"
                lines.append(f"- exclude_taxa: removed {', '.join(operation['removed'])}; samples left empty: "
                             f"{emptied} — {operation['reason']}")
            elif operation["op"] == "join_metadata":
                dropped = ", ".join(operation["dropped_unmatched"]) or "none"
                lines.append(f"- metadata joined on exact IDs; unmatched metadata rows dropped: {dropped}")
    for analysis in spec.analyses:
        if analysis.id not in runs:
            continue
        run_dir = runs[analysis.id]["run_dir"]
        result = json.loads((directory / run_dir / "results.json").read_text())
        lines += ["", f"## Analysis `{analysis.id}` ({result['method']}, dataset `{analysis.dataset}`)", ""]
        for item in (w for w in filters if w["analysis"] == analysis.id):
            lines.append(f"- **row filter `{item['code']}`**: {item['op']} (operation {item['operation_index']}) removed "
                         f"{item['complete_pairs_removed']} complete {item['x']}/{item['y']} pairs "
                         f"(rows {', '.join(item['removed_rows'])}); recorded reason: \"{item['reason']}\". "
                         "Confirm it applies to this analysis (`manifest.json#row_filter_warnings`).")
        for key, value in summary(result).items():
            if key in ("method", "warnings", "excluded"):
                continue
            lines.append(f"- {key} = {json.dumps(value)} (`{run_dir}/results.json#{key}`)")
        for warning in result["warnings"]:
            lines.append(f"- warning `{warning['code']}`: {warning['message']}")
        for item in result["excluded"]:
            lines.append(f"- excluded by the method: {json.dumps(item)}")
        if result.get("limitations"):
            lines.append(f"- limitations: {'; '.join(map(str, result['limitations']))}")
    return "\n".join(lines) + "\n"


def inspect_study(study_dir):
    """Verify integrity, every run bundle, and that derived data recompute exactly from saved inputs."""
    directory = Path(study_dir).resolve()
    try:
        for parent, folders, filenames in os.walk(directory, followlinks=False):
            for entry in (*folders, *filenames):
                path = Path(parent) / entry
                if path.is_symlink() or not (path.is_dir() or path.is_file()):
                    raise ValueError(f"Study contains a link or special file: {path.relative_to(directory)}")
        manifest = json.loads((directory / "manifest.json").read_text())
        if (not isinstance(manifest, dict) or set(manifest) != MANIFEST_KEYS
                or type(manifest["study_version"]) is not int or manifest["study_version"] != STUDY_VERSION):
            raise ValueError("Not a supported study manifest")
        present = {p.relative_to(directory).as_posix() for p in directory.rglob("*")
                   if p.is_file() and p.relative_to(directory).parts[0] != "runs"} - {"manifest.json"}
        if present != set(manifest["files"]):
            raise ValueError("Study file set differs from manifest")
        data = {}
        for name, digest in manifest["files"].items():
            relative = PurePosixPath(name)
            path = directory / name
            if relative.is_absolute() or ".." in relative.parts or path.is_symlink():
                raise ValueError("Unsafe study path")
            data[name] = path.read_bytes()
            if _sha(data[name]) != digest:
                raise ValueError(f"Study integrity failure: {name}")
        spec = StudySpec.model_validate_json(data["study.json"])
        steps = manifest["steps"]
        if [step["id"] for step in steps] != spec.step_ids():
            raise ValueError("Recorded steps differ from the study's declared steps")
        statuses = [step["status"] for step in steps]
        first = next((i for i, status in enumerate(statuses) if status != "complete"), len(statuses))
        if statuses[first:] and statuses[first:] != ["failed"] + ["not_run"] * (len(statuses) - first - 1):
            raise ValueError("Step statuses must be complete steps, then at most one failure followed by not_run")
        if manifest["status"] != ("complete" if first == len(statuses) else "partial"):
            raise ValueError("Study status differs from its steps")
        if set(manifest["runs"]) != {step["id"].split(":", 1)[1] for step in steps
                                     if step["id"].startswith("analysis:") and step["status"] == "complete"}:
            raise ValueError("Run records differ from completed analyses")
        raw = {name: data[f"inputs/{name}"] for name in spec.inputs}
        for name in spec.inputs:
            if spec.inputs[name].path != Path(f"inputs/{name}"):
                raise ValueError("Saved study must reference its input snapshots")
        records = {}
        for step in manifest["steps"]:
            kind, _, name = step["id"].partition(":")
            if kind == "dataset" and step["status"] == "complete":
                files, records[name] = derive(spec, raw, name)
                files[f"{name}.json"] = _json(records[name])
                for filename, expected in files.items():
                    if data.get(f"derived/{filename}") != expected:
                        raise ValueError(f"Derived file does not recompute: {filename}")
        filters = row_filter_warnings(spec, raw, records)
        if manifest["row_filter_warnings"] != filters:
            raise ValueError("Row-filter warnings do not recompute from the saved inputs")
        verified = {}
        # runs/ holds exactly runs/<analysis id>/<run id> for each completed analysis, and nothing else.
        runs_root = directory / "runs"
        level1 = set(runs_root.iterdir()) if runs_root.is_dir() else set()
        level2 = {p for d in level1 if d.is_dir() for p in d.iterdir()}
        declared = {directory / item["run_dir"] for item in manifest["runs"].values()}
        if (any(PurePosixPath(item["run_dir"]).parts[:2] != ("runs", analysis_id) or len(PurePosixPath(item["run_dir"]).parts) != 3
                for analysis_id, item in manifest["runs"].items())
                or level1 != {path.parent for path in declared} or level2 != declared):
            raise ValueError("Run directories differ from manifest")
        analyses = {analysis.id: analysis for analysis in spec.analyses}
        for analysis_id, item in manifest["runs"].items():
            run_dir = directory / item["run_dir"]
            if _sha((run_dir / "manifest.json").read_bytes()) != item["manifest_sha256"]:
                raise ValueError(f"Run manifest differs from study record: {analysis_id}")
            record = inspect_run(run_dir)
            analysis = analyses[analysis_id]
            dataset = analysis.dataset
            if (run_dir / "input.dat").read_bytes() != (directory / "derived" / f"{dataset}.dat").read_bytes():
                raise ValueError(f"Run input is not its declared dataset: {analysis_id}")
            if spec.datasets[dataset].metadata is not None and (run_dir / "metadata.csv").read_bytes() != \
                    (directory / "derived" / f"{dataset}-metadata.csv").read_bytes():
                raise ValueError(f"Run metadata is not its declared dataset: {analysis_id}")
            if (record["specification"].get("metadata") is None) != (spec.datasets[dataset].metadata is None):
                raise ValueError(f"Run metadata provenance differs from its dataset: {analysis_id}")
            saved = {k: v for k, v in record["specification"].items() if k not in ("input", "metadata")}
            placeholders = {"input": "x", **({"metadata": "x"} if spec.datasets[dataset].metadata is not None else {})}
            declared = {k: v for k, v in parse_spec(dict(analysis.spec, **placeholders)).model_dump(mode="json").items()
                        if k not in ("input", "metadata")}
            if saved != declared:
                raise ValueError(f"Run specification differs from the study: {analysis_id}")
            verified[analysis_id] = {"run_dir": item["run_dir"], "summary": summary(record["result"])}
        if data["report.md"] != report(spec, records, manifest["runs"], steps, directory, filters).encode():
            raise ValueError("Study report does not recompute from the verified records")
    except AnalysisError as exc:
        raise AnalysisError("invalid_study", "A study run failed verification", study_dir=str(directory),
                            reason=str(exc), method_error=exc.code) from exc
    except (OSError, ValueError, KeyError, TypeError, ValidationError) as exc:
        raise AnalysisError("invalid_study", "Study could not be verified", study_dir=str(directory), reason=str(exc)) from exc
    return {"status": "verified", "study_status": manifest["status"], "study_dir": str(directory),
            "steps": manifest["steps"], "runs": verified, "row_filter_warnings": filters,
            "scope": "Integrity, preparation recomputation and run provenance verified; scientific validity is separate"}


def reproduce_study(study_dir, output_root):
    """Rerun a verified study from its saved inputs and compare every analysis."""
    from .methods import compare_results
    original = inspect_study(study_dir)
    directory = Path(original["study_dir"])
    require_outside(output_root, directory)
    spec = json.loads((directory / "study.json").read_text())
    fresh = run_study(spec, output_root, base_dir=directory)

    def outcomes(steps):
        return [(step["id"], step["status"], step.get("error", {}).get("code")) for step in steps]

    if outcomes(fresh["steps"]) != outcomes(original["steps"]):
        return {"status": "different", "original": str(directory), "new": fresh["study_dir"],
                "differences": ["steps"]}
    recreated = inspect_study(fresh["study_dir"])
    differences = {}
    if recreated["row_filter_warnings"] != original["row_filter_warnings"]:
        differences["row_filter_warnings"] = ["row-filter warnings differ"]
    for analysis_id, item in original["runs"].items():
        a = json.loads((directory / item["run_dir"] / "results.json").read_text())
        b = json.loads((Path(fresh["study_dir"]) / recreated["runs"][analysis_id]["run_dir"] / "results.json").read_text())
        found, _ = compare_results(a, b)
        if found:
            differences[analysis_id] = found
    derived_same = all((directory / "derived" / p.name).read_bytes() == p.read_bytes()
                       for p in (Path(fresh["study_dir"]) / "derived").iterdir()) if (directory / "derived").exists() else True
    return {"status": "reproduced" if not differences and derived_same else "different",
            "original": str(directory), "new": fresh["study_dir"], "differences": differences,
            "derived_identical": derived_same,
            "scope": "Preparation recomputed byte for byte and numerical outputs compared; interpretation is not verified"}


def study_schema():
    return StudySpec.model_json_schema()
