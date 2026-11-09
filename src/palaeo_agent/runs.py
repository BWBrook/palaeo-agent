"""Self-contained evidence bundles and method-specific reproduction checks."""

import hashlib
import importlib.metadata
import json
from pathlib import Path, PurePosixPath
import platform
import sys
import uuid

from pydantic import Field, model_validator

from .core import AnalysisError, ResultItem
from .methods import (
    MEASUREMENT_METHODS, PLOT_FILES, calculate_method, compare_results, parse_spec, read_inputs, required_files,
    steps_for, summary, table_files, validate_result,
)


class LockfileRecord(ResultItem):
    available: bool
    path: str | None
    reason: str = Field(min_length=1)

    @model_validator(mode="after")
    def consistent_lock(self):
        if self.available != (self.path == "uv.lock") or (not self.available and self.path is not None):
            raise ValueError("Lockfile availability and path disagree")
        return self


class RunEnvironment(ResultItem):
    python: str = Field(min_length=1)
    platform: str = Field(min_length=1)
    packages: dict[str, str]
    distributions: list[dict[str, str]]
    implementation_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    source_files_sha256: dict[str, str]
    lockfile: LockfileRecord
    rng: str = Field(min_length=1)

    @model_validator(mode="after")
    def consistent_environment(self):
        if not {"palaeo-agent", "numpy", "pydantic", "matplotlib"} <= self.packages.keys():
            raise ValueError("Required dependency versions are missing")
        if not self.distributions or any(set(item) != {"name", "version"} or not all(item.values())
                                         for item in self.distributions):
            raise ValueError("Installed distribution records are missing or malformed")
        if any({"name": name, "version": version} not in self.distributions
               for name, version in self.packages.items()):
            raise ValueError("Package versions disagree with installed distribution records")
        if not self.source_files_sha256:
            raise ValueError("Implementation source fingerprints are missing")
        if any(len(value) != 64 or any(char not in "0123456789abcdef" for char in value)
               for value in self.source_files_sha256.values()):
            raise ValueError("Invalid source fingerprint")
        if _sha(json.dumps(self.source_files_sha256, sort_keys=True).encode()) != self.implementation_sha256:
            raise ValueError("Implementation fingerprint does not match its source-file map")
        return self


class ArtifactRecord(ResultItem):
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    bytes: int = Field(ge=0)
    media_type: str = Field(min_length=1)
    produced_by: str = Field(min_length=1)


class InputSnapshot(ResultItem):
    path: str = Field(min_length=1)
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    bytes: int = Field(ge=0)


class RunStep(ResultItem):
    id: str = Field(min_length=1)
    inputs: list[str]
    outputs: list[str]


class RunManifest(ResultItem):
    schema_version: int
    status: str
    run_id: str = Field(min_length=1)
    method: str
    method_version: int
    inputs: dict[str, InputSnapshot]
    steps: list[RunStep]
    files: dict[str, ArtifactRecord]

    @model_validator(mode="after")
    def coherent_provenance(self):
        if self.schema_version != 2 or self.status != "complete":
            raise ValueError("Unsupported completion record")
        available, step_ids = set(), set()
        for step in self.steps:
            if step.id in step_ids or not set(step.inputs) <= available:
                raise ValueError("Invalid step order or duplicate step ID")
            if any(name in available for name in step.outputs):
                raise ValueError("An artefact has more than one producing step")
            if any(name not in self.files or self.files[name].produced_by != step.id for name in step.outputs):
                raise ValueError("Artefact producer differs from step provenance")
            available.update(step.outputs)
            step_ids.add(step.id)
        if available != set(self.files):
            raise ValueError("Step provenance must account for every artefact")
        for source in self.inputs.values():
            if source.path not in self.files:
                raise ValueError("Input snapshot is not an artefact")
            artifact = self.files[source.path]
            if (artifact.sha256, artifact.bytes) != (source.sha256, source.bytes):
                raise ValueError("Input snapshot fingerprint differs from artefact")
        return self


def _json(path, value):
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def _sha(data):
    return hashlib.sha256(data).hexdigest()


def _checkout_lock():
    source = Path(__file__).resolve().parent
    candidate = source.parents[1] / "uv.lock"
    if source.parent.name == "src" and (candidate.parent / "pyproject.toml").is_file() and candidate.is_file():
        return candidate.read_bytes()
    return None


# Captured once, when the package is imported, so a long-lived process (the MCP server) records the
# code and lockfile it actually loaded rather than whatever is on disk when a run happens.
_SOURCE_HASHES = {path.name: _sha(path.read_bytes()) for path in sorted(Path(__file__).parent.glob("*.py"))}
_LOCK = _checkout_lock()


def _find_lockfile():
    """The checkout lockfile bytes captured at import, or None."""
    return _LOCK


def _rng_description(result):
    if result is not None and result["method"] == "count_homogeneity":
        randomization = result["randomization"]
        return (f"NumPy Generator({randomization['bit_generator']}), seed={randomization['seed']}; "
                "SeedSequence.spawn in declared pair order; SciPy random_table patefield; "
                "settings saved in randomization.json")
    if result is not None and result["method"] == "rma_paired":
        bootstrap = result["bootstrap"]
        return (f"NumPy Generator({bootstrap['bit_generator']}), seed={bootstrap['seed']}; {bootstrap['draw']}; "
                "replicate slopes saved in bootstrap.csv")
    if result is None or result["method"] != "permanova":
        return "not used; deterministic method"
    permutation = result["permutation"]
    if permutation["mode"] == "exact":
        return "not used; exact labelled group allocations enumerated"
    return (f"NumPy Generator({permutation['bit_generator']}), seed={permutation['seed']}; "
            "actual index schedule saved in permutations.json")


def _environment(lock, result=None):
    hashes = _SOURCE_HASHES
    packages, distributions = {}, []
    for distribution in importlib.metadata.distributions():
        name = distribution.metadata.get("Name")
        if name:
            name = name.lower().replace("_", "-")
            packages.setdefault(name, distribution.version)
            distributions.append({"name": name, "version": distribution.version})
    return RunEnvironment.model_validate({
        "python": sys.version, "platform": platform.platform(), "packages": dict(sorted(packages.items())),
        "distributions": sorted(distributions, key=lambda item: (item["name"], item["version"])),
        "implementation_sha256": _sha(json.dumps(hashes, sort_keys=True).encode()),
        "source_files_sha256": hashes, "rng": _rng_description(result),
        "lockfile": {"available": lock is not None, "path": "uv.lock" if lock else None,
                     "reason": "Project checkout lockfile captured" if lock else
                     "No checkout lockfile available; all installed distribution versions recorded"},
    }).model_dump(mode="json")


def _plot(path, result, spec):
    if spec.method == "community":
        from .community import plot_community
        return plot_community(path, result, spec)
    if spec.method == "permanova":
        return _plot_permanova(path, result)
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


def _plot_permanova(path, result):
    import matplotlib
    matplotlib.use("Agg")
    from matplotlib import pyplot as plt
    import numpy as np

    permutation = result["permutation"]
    finite = [value for value in permutation["statistics"] if value is not None]
    fig, axes = plt.subplots(1, 2, figsize=(10, 4), layout="constrained")
    if finite:
        axes[0].hist(finite, bins=min(20, max(1, len(finite))), color="steelblue", alpha=.75)
    axes[0].axvline(result["pseudo_f"], color="black", label="Observed pseudo-F")
    axes[0].legend()
    mode = "Exact allocations" if permutation["mode"] == "exact" else "Monte Carlo permutations"
    axes[0].set(xlabel="Pseudo-F (finite allocations)", ylabel="Allocations", title=mode)
    axes[0].text(.97, .95, f"p = {result['p_value']:.5g}\nPositive infinity: {permutation['infinite_count']}",
                 ha="right", va="top", transform=axes[0].transAxes,
                 bbox={"facecolor": "white", "edgecolor": "none", "alpha": .85})
    distances = result["dispersion"]["distances"]
    for position, group in enumerate(result["group_labels"]):
        values = [distance for distance, label in zip(distances, result["groups"], strict=True) if label == group]
        jitter = np.linspace(-.12, .12, len(values)) if len(values) > 1 else [0]
        axes[1].scatter(position + np.asarray(jitter), values, color=f"C{position % 10}", s=18)
        mean = result["dispersion"]["group_mean_distances"][group]
        axes[1].plot([position - .18, position + .18], [mean, mean], color="black")
    axes[1].set_xticks(range(len(result["group_labels"])), result["group_labels"])
    axes[1].set(xlabel=result["group_column"], ylabel="Distance to group centroid",
                title="Descriptive dispersion (no test)")
    axes[1].set_ylim(0, max(distances) * 1.1 if max(distances) > 0 else 1)
    fig.savefig(path, format="svg", metadata={"Date": None})
    fig.savefig(path.with_suffix(".png"), format="png", dpi=150)
    plt.close(fig)


def require_outside(output_root, *bundles):
    """Refuse an output location inside a bundle being read: writing there would change that evidence."""
    output = Path(output_root).resolve()
    for bundle in bundles:
        if output.is_relative_to(Path(bundle).resolve()):
            raise AnalysisError("output_inside_bundle", "The output location must not be inside a bundle it reads",
                                output=str(output), bundle=str(Path(bundle).resolve()))


def run(spec, output_root: str | Path):
    spec = parse_spec(spec)
    inputs = read_inputs(spec)
    result = validate_result(spec, calculate_method(spec, inputs))
    directory = Path(output_root).resolve() / uuid.uuid4().hex
    try:
        directory.mkdir(parents=True, exist_ok=False)
        snapshots = {}
        for role, data in inputs.items():
            filename = "metadata.csv" if role == "metadata" else "input.dat"
            (directory / filename).write_bytes(data)
            snapshots[role] = {"path": filename, "sha256": _sha(data), "bytes": len(data)}
        portable = spec.model_copy(update={"input": Path("input.dat")})
        if getattr(spec, "metadata", None) is not None:
            portable = portable.model_copy(update={"metadata": Path("metadata.csv")})
        _json(directory / "spec.json", portable.model_dump(mode="json"))
        _json(directory / "results.json", result)
        for name, data in table_files(result).items():
            (directory / name).write_bytes(data)
        lock = _find_lockfile()
        _json(directory / "environment.json", _environment(lock, result))
        if lock is not None:
            (directory / "uv.lock").write_bytes(lock)
        if PLOT_FILES <= required_files(spec):
            _plot(directory / "diagnostics.svg", result, spec)
        steps = steps_for(spec, lock is not None)
        producers = {filename: step["id"] for step in steps for filename in step["outputs"]}
        media_types = {".json": "application/json", ".csv": "text/csv", ".svg": "image/svg+xml", ".png": "image/png",
                       ".dat": "text/plain", ".lock": "text/plain"}
        files = {path.name: {"sha256": _sha(path.read_bytes()), "bytes": path.stat().st_size,
                             "media_type": media_types.get(path.suffix, "application/octet-stream"),
                             "produced_by": producers[path.name]}
                 for path in sorted(directory.iterdir()) if path.is_file()}
        manifest = RunManifest.model_validate({"schema_version": 2, "status": "complete", "run_id": directory.name,
                    "method": spec.method, "method_version": result["method_version"], "inputs": snapshots,
                    "steps": steps, "files": files})
        _json(directory / "manifest.json", manifest.model_dump(mode="json"))
    except Exception as exc:
        if directory.is_dir():
            _json(directory / "failure.json", {"status": "failed", "error_type": type(exc).__name__, "message": str(exc)})
        if isinstance(exc, AnalysisError):
            raise
        raise AnalysisError("bundle_write_failed", "Run did not complete", run_dir=str(directory), reason=str(exc)) from exc
    return {"status": "complete", "run_dir": str(directory), "summary": summary(result)}


def inspect_run(run_dir: str | Path):
    directory = Path(run_dir).resolve()
    try:
        path = directory / "manifest.json"
        if path.is_symlink():
            raise ValueError("Manifest must not be a symbolic link")
        raw = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(raw, dict) and raw.get("schema_version") != 2:
            raise AnalysisError("unsupported_schema", "Only run schema 2 is supported; retain older evidence with its producing revision",
                                schema_version=raw.get("schema_version"))
        manifest = RunManifest.model_validate(raw).model_dump(mode="json")
        names = set(manifest["files"])
        if {item.name for item in directory.iterdir()} != names | {"manifest.json"}:
            raise ValueError("Bundle file set differs from manifest")
        data = {}
        for name, expected in manifest["files"].items():
            relative = PurePosixPath(name)
            artifact = directory / name
            if relative.is_absolute() or len(relative.parts) != 1 or "\\" in name or artifact.is_symlink() or not artifact.is_file():
                raise ValueError("Unsafe artefact path")
            data[name] = artifact.read_bytes()
            if _sha(data[name]) != expected["sha256"] or len(data[name]) != expected["bytes"]:
                raise ValueError(f"Artefact integrity failure: {name}")
        spec = parse_spec(json.loads(data["spec.json"]))
        if spec.input != Path("input.dat"):
            raise ValueError("Saved specification must reference its input snapshot")
        expected_roles = {"measurements" if spec.method in MEASUREMENT_METHODS else "matrix": "input.dat"}
        if getattr(spec, "metadata", None) is not None:
            if spec.metadata != Path("metadata.csv"):
                raise ValueError("Saved metadata must reference its snapshot")
            expected_roles["metadata"] = "metadata.csv"
        if {role: item["path"] for role, item in manifest["inputs"].items()} != expected_roles:
            raise ValueError("Named input roles differ from the saved specification")
        if manifest["steps"] != steps_for(spec, "uv.lock" in names):
            raise ValueError("Recorded steps differ from the method's declared steps")
        result = validate_result(spec, json.loads(data["results.json"]))
        if manifest["method"] != spec.method or manifest["method_version"] != result["method_version"]:
            raise ValueError("Manifest method identity differs from saved records")
        changed = sorted(name for name, expected in table_files(result).items() if data[name] != expected)
        if changed:
            raise ValueError(f"Derived tables differ from the validated result: {', '.join(changed)}")
        environment = RunEnvironment.model_validate_json(data["environment.json"]).model_dump(mode="json")
        if environment["lockfile"]["available"] != ("uv.lock" in names):
            raise ValueError("Lockfile provenance differs from saved artefacts")
        if environment["rng"] != _rng_description(result):
            raise ValueError("RNG provenance differs from the method result")
        if spec.method == "rma_paired" and result["bootstrap"]["numpy_version"] != environment["packages"]["numpy"]:
            raise ValueError("Bootstrap NumPy version differs from its recorded environment")
        if spec.method == "permanova" and result["permutation"]["numpy_version"] != environment["packages"]["numpy"]:
            raise ValueError("Permutation NumPy version differs from its recorded environment")
        if spec.method == "count_homogeneity" and any(
                result["randomization"][package + "_version"] != environment["packages"].get(package)
                for package in ("numpy", "scipy")):
            raise ValueError("Sampling library version differs from its recorded environment")
    except AnalysisError as exc:
        if exc.code == "unsupported_schema":
            raise
        raise AnalysisError("invalid_bundle", "Bundle record failed method validation", run_dir=str(directory),
                            reason=str(exc), method_error=exc.code) from exc
    except (OSError, ValueError, KeyError, TypeError) as exc:
        raise AnalysisError("invalid_bundle", "Bundle could not be verified", run_dir=str(directory), reason=str(exc)) from exc
    return {"status": "verified", "run_dir": str(directory), "manifest": manifest, "result": result,
            "specification": spec.model_dump(mode="json"), "environment": environment,
            "scope": "Artefact integrity and record structure verified; scientific validity and authenticity are separate questions"}


def reproduce(run_dir: str | Path, output_root: str | Path):
    original = inspect_run(run_dir)
    directory = Path(original["run_dir"])
    require_outside(output_root, directory)
    spec = parse_spec(original["specification"])
    updates = {"input": directory / "input.dat"}
    if getattr(spec, "metadata", None) is not None:
        updates["metadata"] = directory / "metadata.csv"
    spec = spec.model_copy(update=updates)
    fresh = run(spec, output_root)
    recreated = inspect_run(fresh["run_dir"])
    differences, policy = compare_results(original["result"], recreated["result"])
    if recreated["manifest"]["inputs"] != original["manifest"]["inputs"]:
        differences.insert(0, "inputs")
    response = {"status": "reproduced" if not differences else "different", "original_run": str(directory),
            "new_run": fresh["run_dir"], "differences": differences,
            "tolerance": {key: policy[key] for key in ("rtol", "atol")},
            "environment_identical": original["environment"] == recreated["environment"],
            "scope": "Recorded numerical outputs compared; this does not verify the scientific interpretation"}
    if "ordination" in policy:
        response["ordination_comparison"] = policy["ordination"]
    return response
