"""Saved evidence bundles and fresh-process reproducibility checks."""

import csv
import hashlib
import importlib.metadata
import json
import math
from pathlib import Path, PurePosixPath
import platform
import sys
import uuid

from pydantic import Field, model_validator

from .core import AnalysisError, RmaResult, RmaSpec, ResultItem, calculate


NUMERICAL_FIELDS = ("mean_x", "mean_y", "sd_x", "sd_y", "correlation", "slope", "intercept", "vertical_residual_rmse")
REPRODUCTION_RTOL = 1e-12
REPRODUCTION_ATOL = 1e-12


class RunEnvironment(ResultItem):
    python: str = Field(min_length=1)
    platform: str = Field(min_length=1)
    packages: dict[str, str]
    implementation_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    source_files_sha256: dict[str, str]
    rng: str = Field(min_length=1)

    @model_validator(mode="after")
    def consistent_environment(self):
        if not {"palaeo-agent", "numpy", "pydantic", "matplotlib"} <= self.packages.keys():
            raise ValueError("Required dependency versions are missing")
        if not self.source_files_sha256:
            raise ValueError("Implementation source fingerprints are missing")
        if any(len(value) != 64 or any(char not in "0123456789abcdef" for char in value)
               for value in self.source_files_sha256.values()):
            raise ValueError("Invalid source fingerprint")
        if _sha(json.dumps(self.source_files_sha256, sort_keys=True).encode()) != self.implementation_sha256:
            raise ValueError("Implementation fingerprint does not match its source-file map")
        return self


def _json(path, value):
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def _sha(data):
    return hashlib.sha256(data).hexdigest()


def _environment():
    source = Path(__file__).parent
    hashes = {path.name: _sha(path.read_bytes()) for path in sorted(source.glob("*.py"))}
    return {"python": sys.version, "platform": platform.platform(),
            "packages": {name: importlib.metadata.version(name)
                         for name in ("palaeo-agent", "numpy", "pydantic", "matplotlib")},
            "implementation_sha256": _sha(json.dumps(hashes, sort_keys=True).encode()),
            "source_files_sha256": hashes, "rng": "not used; deterministic method"}


def _plot(path, result, spec):
    import matplotlib
    matplotlib.use("Agg")
    from matplotlib import pyplot as plt
    rows = result["pairs"]
    xx, yy = [row["x"] for row in rows], [row["y"] for row in rows]
    fig, axes = plt.subplots(1, 2, figsize=(9, 4), layout="constrained")
    axes[0].scatter(xx, yy, s=14)
    endpoints = [min(xx), max(xx)]
    axes[0].plot(endpoints, [result["intercept"] + result["slope"] * value for value in endpoints])
    label = "log10 " if spec.transform == "log10" else ""
    axes[0].set(xlabel=label + spec.x, ylabel=label + spec.y, title="Reduced major axis")
    axes[1].scatter(xx, [row["residual"] for row in rows], s=14)
    axes[1].axhline(0, color="grey", linewidth=1)
    axes[1].set(xlabel=label + spec.x, ylabel="Vertical residual", title="Descriptive diagnostic")
    fig.savefig(path, format="svg", metadata={"Date": None})
    fig.savefig(path.with_suffix(".png"), format="png", dpi=150)
    plt.close(fig)


def run(spec: RmaSpec | dict, output_root: str | Path):
    spec = spec if isinstance(spec, RmaSpec) else RmaSpec.model_validate(spec)
    try:
        data = spec.input.read_bytes()
    except OSError as exc:
        raise AnalysisError("input_unreadable", "Cannot read input file", path=str(spec.input), reason=str(exc)) from exc
    result = calculate(spec, data)
    directory = Path(output_root).resolve() / uuid.uuid4().hex
    try:
        directory.mkdir(parents=True, exist_ok=False)
        (directory / "input.dat").write_bytes(data)
        portable = spec.model_copy(update={"input": Path("input.dat")})
        _json(directory / "spec.json", portable.model_dump(mode="json"))
        _json(directory / "results.json", result)
        with (directory / "used-pairs.csv").open("w", newline="", encoding="utf-8") as stream:
            writer = csv.DictWriter(stream, fieldnames=list(result["pairs"][0]))
            writer.writeheader()
            writer.writerows(result["pairs"])
        _json(directory / "environment.json", _environment())
        lock = Path(__file__).resolve().parents[2] / "uv.lock"
        if lock.is_file():
            (directory / "uv.lock").write_bytes(lock.read_bytes())
        _plot(directory / "diagnostics.svg", result, spec)
        media_types = {".json": "application/json", ".csv": "text/csv", ".svg": "image/svg+xml", ".png": "image/png",
                       ".dat": "text/plain", ".lock": "text/plain"}
        files = {path.name: {"sha256": _sha(path.read_bytes()), "bytes": path.stat().st_size,
                             "media_type": media_types.get(path.suffix, "application/octet-stream")}
                 for path in sorted(directory.iterdir()) if path.is_file()}
        _json(directory / "manifest.json", {"schema_version": 1, "status": "complete",
              "run_id": directory.name, "input_sha256": _sha(data), "files": files})
    except Exception as exc:
        if directory.is_dir():
            _json(directory / "failure.json", {"status": "failed", "error_type": type(exc).__name__, "message": str(exc)})
        if isinstance(exc, AnalysisError):
            raise
        raise AnalysisError("bundle_write_failed", "Run did not complete", run_dir=str(directory), reason=str(exc)) from exc
    return {"status": "complete", "run_dir": str(directory),
            "summary": {key: result[key] for key in ("n", "n_input", "slope", "intercept", "correlation", "excluded", "warnings")}}


def inspect_run(run_dir: str | Path):
    directory = Path(run_dir).resolve()
    try:
        if (directory / "manifest.json").is_symlink():
            raise ValueError("Manifest must not be a symbolic link")
        manifest = json.loads((directory / "manifest.json").read_text(encoding="utf-8"))
        if not isinstance(manifest, dict) or not isinstance(manifest.get("files"), dict):
            raise ValueError("Invalid manifest structure")
        if manifest["schema_version"] != 1 or manifest["status"] != "complete":
            raise ValueError("Missing completion state")
        names = set(manifest["files"])
        required = {"input.dat", "spec.json", "results.json", "used-pairs.csv", "environment.json", "diagnostics.svg", "diagnostics.png"}
        if not required <= names:
            raise ValueError("Missing required artefact entries")
        actual = {item.name for item in directory.iterdir()}
        if actual != names | {"manifest.json"}:
            raise ValueError("Bundle file set differs from manifest")
        for name, expected in manifest["files"].items():
            if not isinstance(expected, dict):
                raise ValueError("Invalid artefact entry")
            relative = PurePosixPath(name)
            path = directory / name
            if relative.is_absolute() or len(relative.parts) != 1 or "\\" in name or path.is_symlink() or not path.is_file():
                raise ValueError("Unsafe artefact path")
            data = path.read_bytes()
            if _sha(data) != expected["sha256"] or len(data) != expected["bytes"]:
                raise ValueError(f"Artefact integrity failure: {name}")
        if manifest["input_sha256"] != manifest["files"]["input.dat"]["sha256"]:
            raise ValueError("Input fingerprint differs from manifest")
        result = RmaResult.model_validate_json((directory / "results.json").read_bytes()).model_dump(mode="json")
        spec = RmaSpec.model_validate_json((directory / "spec.json").read_bytes())
        if spec.input != Path("input.dat"):
            raise ValueError("Saved specification must reference its input snapshot")
        if spec.x == spec.y:
            raise ValueError("Saved specification must select distinct measurement columns")
        if any(getattr(spec, key) != result[key] for key in ("method", "transform", "missing")):
            raise ValueError("Saved specification and result describe different analyses")
        environment = RunEnvironment.model_validate_json((directory / "environment.json").read_bytes()).model_dump(mode="json")
    except (OSError, ValueError, KeyError, TypeError) as exc:
        raise AnalysisError("invalid_bundle", "Bundle could not be verified", run_dir=str(directory), reason=str(exc)) from exc
    return {"status": "verified", "run_dir": str(directory), "manifest": manifest, "result": result,
            "specification": spec.model_dump(mode="json"), "environment": environment,
            "scope": "Artefact integrity and record structure verified; scientific validity and authenticity are separate questions"}


def reproduce(run_dir: str | Path, output_root: str | Path):
    original = inspect_run(run_dir)
    directory = Path(original["run_dir"])
    spec = RmaSpec.model_validate(original["specification"])
    spec = spec.model_copy(update={"input": directory / "input.dat"})
    fresh = run(spec, output_root)
    recreated = inspect_run(fresh["run_dir"])["result"]
    expected = original["result"]
    differences = [key for key in NUMERICAL_FIELDS if not math.isclose(
        recreated[key], expected[key], rel_tol=REPRODUCTION_RTOL, abs_tol=REPRODUCTION_ATOL)]
    for key in ("n", "n_input", "excluded", "transform", "missing"):
        if recreated[key] != expected[key]:
            differences.append(key)
    if len(recreated["pairs"]) != len(expected["pairs"]):
        differences.append("pairs")
    else:
        for index, (left, right) in enumerate(zip(recreated["pairs"], expected["pairs"], strict=True)):
            if left["sample_id"] != right["sample_id"]:
                differences.append(f"pairs[{index}].sample_id")
            for key in ("x_raw", "y_raw", "x", "y", "residual"):
                if not math.isclose(left[key], right[key], rel_tol=REPRODUCTION_RTOL, abs_tol=REPRODUCTION_ATOL):
                    differences.append(f"pairs[{index}].{key}")
    environment = original["environment"]
    current = inspect_run(fresh["run_dir"])["environment"]
    return {"status": "reproduced" if not differences else "different", "original_run": str(directory),
            "new_run": fresh["run_dir"], "differences": differences,
            "tolerance": {"rtol": REPRODUCTION_RTOL, "atol": REPRODUCTION_ATOL},
            "environment_identical": environment == current,
            "scope": "Recorded numerical outputs compared; this does not verify the scientific interpretation"}
