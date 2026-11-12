"""Root-scoped MCP transport over the existing scientific operations."""

import argparse
import asyncio
import json
from pathlib import Path
import sys
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from .core import AnalysisError
from .methods import INPUT_FORMATS, MethodSpec, METHOD_INDEX, discover, summary, validate
from .primer import primer, primer_metadata
from .runs import inspect_run, reproduce, run
from .sensitivity import compare_community_runs, inspect_comparison
from .study import StudySpec, inspect_study, reproduce_study, run_study
from .neotoma import NeotomaSpec, inspect_neotoma, neotoma_extract, reproduce_neotoma


SERVER_INSTRUCTIONS = (
    "Before any analysis, call the primer tool and read its full text. Follow that primer for the session: "
    "use a suitable Palaeo-Agent API operation for every supported analytical subtask; "
    "never bypass it with bespoke code. Assess scientific suitability, and declare unsupported "
    "parts or demonstrated defects. Discover method scopes and schemas before running analyses."
)


class Request(BaseModel):
    model_config = ConfigDict(extra="forbid")


class DiscoverRequest(Request):
    method: Literal["rma", "rma_paired", "community", "permanova", "rarefaction", "count_homogeneity", "coniss"] | None = None


class ValidateRequest(Request):
    spec: MethodSpec


class RunRequest(ValidateRequest):
    output: str = "runs"


class BundleRequest(Request):
    bundle: str


class ReproduceRequest(BundleRequest):
    output: str = "runs"


class CompareRequest(Request):
    baseline: str
    sensitivity: str
    output: str = "comparisons"


class StudyRunRequest(Request):
    study: StudySpec
    output: str = Field(min_length=1, description="New directory for the study bundle")


class StudyRequest(Request):
    study_dir: str


class StudyReproduceRequest(StudyRequest):
    output: str = Field(min_length=1)


class NeotomaExtractRequest(Request):
    spec: NeotomaSpec
    output: str = Field(default="extractions", min_length=1)


class ResultRequest(BundleRequest):
    field: str = Field(min_length=1, description="Dot-separated result-field path; discover fields with inspect")
    offset: int = Field(default=0, ge=0, strict=True)
    limit: int = Field(default=25, ge=1, le=100, strict=True)
    column_offset: int = Field(default=0, ge=0, strict=True)
    column_limit: int = Field(default=25, ge=1, le=100, strict=True)


REQUESTS = {
    "primer": (Request, "Read the full versioned agent primer before any analysis; returns exact text and its SHA-256."),
    "discover": (DiscoverRequest, "List method summaries, or request one method's complete typed schemas."),
    "validate": (ValidateRequest, "Validate declared data and numerical requirements; sampling assumptions are not established."),
    "run": (RunRequest, "Read the primer first. Run a declared analysis and save a self-contained evidence bundle."),
    "inspect": (BundleRequest, "Verify a run's integrity and return a compact summary, field names and artifact references."),
    "reproduce": (ReproduceRequest, "Recompute a saved bundle and compare its numerical outputs."),
    "compare": (CompareRequest, "Compare community runs descriptively under the existing provenance and one-factor rules."),
    "inspect_comparison": (BundleRequest, "Verify a descriptive comparison and both embedded run bundles."),
    "result": (ResultRequest, "Read one verified run-result field, with bounded rows and matrix columns."),
    "study_run": (StudyRunRequest, "Read the primer first. Run a multi-step study: declared preparation, then analyses; saves one bundle."),
    "study_inspect": (StudyRequest, "Verify a study's integrity, recompute its prepared data and verify every run."),
    "study_reproduce": (StudyReproduceRequest, "Rerun a verified study from its saved inputs and compare every analysis."),
    "neotoma_extract": (NeotomaExtractRequest, "Extract a saved Neotoma download (declared datasets, units, filters, zero-fill, row order) into a portable intake bundle; selection, overrides, harmonisation and closure stay with the caller."),
    "neotoma_inspect": (BundleRequest, "Verify an extraction bundle by re-deriving every file from its bundled source snapshot."),
    "neotoma_reproduce": (ReproduceRequest, "Re-extract a verified extraction bundle and compare derived files byte for byte."),
}


COMPACT_SPEC = {"type": "object", "required": ["method"], "additionalProperties": True,
                "properties": {"method": {"enum": ["rma", "rma_paired", "community", "permanova", "rarefaction", "count_homogeneity", "coniss"]}},
                "description": "A complete method specification. Its exact schema comes from "
                               "the discover tool with that method; invalid specifications are refused with details."}


def _schema(model):
    """Advertised input schema. The method spec union is replaced by a reference to discovery; the
    server still validates every call against the full typed model."""
    schema = model.model_json_schema()
    if issubclass(model, ValidateRequest):
        schema["properties"]["spec"] = COMPACT_SPEC
        schema.pop("$defs", None)
    return schema


def tool_definitions():
    return [{"name": name, "description": description, "inputSchema": _schema(model)}
            for name, (model, description) in REQUESTS.items()]


def _compact_summary(value):
    return {key: ({"count": len(item), "first": item[:25], "truncated": True}
                  if isinstance(item, list) and len(item) > 25 else item)
            for key, item in value.items()}


class Transport:
    def __init__(self, root: str | Path):
        self.root = Path(root).resolve(strict=True)
        if not self.root.is_dir():
            raise ValueError("Session root must be an existing directory")

    def _path(self, value):
        path = Path(value)
        path = (self.root / path).resolve() if not path.is_absolute() else path.resolve()
        if not path.is_relative_to(self.root):
            raise AnalysisError("path_outside_root", "Path is outside the session root")
        return path

    def _relative(self, value):
        return self._path(value).relative_to(self.root).as_posix()

    def _spec(self, spec):
        updates = {"input": self._path(spec.input)}
        if getattr(spec, "metadata", None) is not None:
            updates["metadata"] = self._path(spec.metadata)
        return spec.model_copy(update=updates)

    def _references(self, directory, manifest):
        return [{"path": self._relative(directory / name), **metadata}
                for name, metadata in manifest["files"].items()]

    def dispatch(self, name: str, arguments: dict):
        try:
            if name not in REQUESTS:
                raise AnalysisError("unknown_tool", "Unknown scientific operation", tool=name)
            request = REQUESTS[name][0].model_validate(arguments)
            result = self._dispatch(name, request)
            if "summary" in result:
                result["summary"] = _compact_summary(result["summary"])
            for key in ("run_dir", "comparison_dir", "original_run", "new_run", "study_dir", "original", "new"):
                if key in result:
                    result[key] = self._relative(result[key])
            return result
        except ValidationError as exc:
            return {"status": "error", "code": "invalid_request", "message": "Request does not match the tool schema",
                    "details": json.loads(exc.json(include_url=False, include_context=False, include_input=False))}
        except AnalysisError as exc:
            return exc.as_dict()
        except (OSError, ValueError, KeyError, TypeError) as exc:
            return {"status": "error", "code": "request_failed", "message": str(exc)}

    def _dispatch(self, name, request):
        if name == "primer":
            return primer()
        if name == "discover":
            if request.method is None:
                return {"method_index": METHOD_INDEX, "input_formats": INPUT_FORMATS,
                        "primer": primer_metadata(),
                        "path_policy": "All paths resolve inside the configured session root; relative paths start there"}
            method = next(item for item in discover()["methods"] if item["id"] == request.method)
            return {**method, "primer": primer_metadata()}
        if name == "validate":
            return validate(self._spec(request.spec))
        if name == "run":
            return run(self._spec(request.spec), self._path(request.output))
        if name == "reproduce":
            return reproduce(self._path(request.bundle), self._path(request.output))
        if name == "compare":
            return compare_community_runs(self._path(request.baseline), self._path(request.sensitivity),
                                          self._path(request.output))
        if name == "study_run":
            study = request.study.model_copy(update={"inputs": {
                key: item.model_copy(update={"path": self._path(item.path)}) for key, item in request.study.inputs.items()}})
            return run_study(study.model_dump(mode="json"), self._path(request.output), base_dir=self.root)
        if name == "study_inspect":
            return inspect_study(self._path(request.study_dir))
        if name == "study_reproduce":
            return reproduce_study(self._path(request.study_dir), self._path(request.output))
        if name == "neotoma_extract":
            spec = request.spec.model_copy(update={"source": Path(self._path(request.spec.source))})
            return neotoma_extract(spec, self._path(request.output))
        if name == "neotoma_inspect":
            record = inspect_neotoma(self._path(request.bundle))
            extract, environment = record["extract"], record["environment"]
            directory = Path(record["bundle"])
            return {"status": record["status"], "bundle": record["bundle"],
                    "summary": {key: extract[key] for key in (
                        "kind", "datasets_selected", "n_samples", "n_labels", "n_age_rows", "data_seen", "data_kept",
                        "dropped", "all_zero_samples", "source_sha256")},
                    "specification": record["specification"],
                    "environment": {"implementation_sha256": environment["implementation_sha256"],
                                    "python": environment["python"].split()[0],
                                    "lockfile_captured": environment["lockfile"]["available"]},
                    "files": sorted(self._relative(path) for path in directory.iterdir()),
                    "scope": record["scope"]}
        if name == "neotoma_reproduce":
            return reproduce_neotoma(self._path(request.bundle), self._path(request.output))
        directory = self._path(request.bundle)
        if name == "inspect_comparison":
            record = inspect_comparison(directory)
            return {"status": record["status"], "comparison_dir": str(directory),
                    "summary": {key: record["report"][key] for key in (
                        "settings_changed", "pearson_distance_correlation", "spearman_distance_correlation",
                        "symmetric_procrustes_m2", "warnings")},
                    "artifacts": self._references(directory, record["manifest"]), "scope": record["scope"]}
        record = inspect_run(directory)
        if name == "inspect":
            return {"status": record["status"], "run_dir": str(directory), "summary": summary(record["result"]),
                    "result_fields": sorted(record["result"]),
                    "artifacts": self._references(directory, record["manifest"]), "scope": record["scope"]}
        value = record["result"]
        for component in request.field.split("."):
            if not isinstance(value, dict) or component not in value:
                raise AnalysisError("unknown_result_field", "Result field does not exist", field=request.field)
            value = value[component]
        response = {"status": "verified", "field": request.field}
        if isinstance(value, dict):
            response["fields"] = sorted(value)
            response["message"] = "Select a child field to read its value"
        elif isinstance(value, list):
            response.update(total=len(value), offset=request.offset, limit=request.limit)
            page = value[request.offset:request.offset + request.limit]
            if any(isinstance(row, list) for row in page):
                response.update(column_offset=request.column_offset, column_limit=request.column_limit,
                                column_totals=[len(row) if isinstance(row, list) else None for row in page])
                page = [row[request.column_offset:request.column_offset + request.column_limit]
                        if isinstance(row, list) else row for row in page]
            response["value"] = page
        else:
            response["value"] = value
        return response


def create_server(root):
    from mcp import types
    from mcp.server import Server

    transport = Transport(root)

    async def list_tools(context, params):
        return types.ListToolsResult(tools=[types.Tool.model_validate(item) for item in tool_definitions()])

    async def call_tool(context, params):
        value = transport.dispatch(params.name, params.arguments or {})
        return types.CallToolResult(
            content=[types.TextContent(type="text", text=json.dumps(value, allow_nan=False))],
            structured_content=value, is_error=value.get("status") == "error")

    return Server("palaeo-agent", version=primer_metadata()["version"], instructions=SERVER_INSTRUCTIONS,
                  on_list_tools=list_tools, on_call_tool=call_tool)


async def serve(root):
    from mcp.server.stdio import stdio_server

    server = create_server(root)
    async with stdio_server() as (read, write):
        await server.run(read, write, server.create_initialization_options())


def main(argv=None):
    parser = argparse.ArgumentParser(description="Root-scoped Palaeo-Agent MCP stdio server")
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--call", choices=REQUESTS, help="Single confined call: JSON arguments on stdin, JSON result on stdout")
    args = parser.parse_args(argv)
    if args.call:
        try:
            result = Transport(args.root).dispatch(args.call, json.load(sys.stdin))
        except (ValueError, OSError) as exc:
            result = {"status": "error", "code": "invalid_request", "message": str(exc)}
        print(json.dumps(result, allow_nan=False))
        return 2 if result.get("status") == "error" else 0
    asyncio.run(serve(args.root))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
