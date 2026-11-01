"""End-to-end replay of an analyst package (docs/sprints-5-6-proposal.md, 5.1). No model is involved.

A fresh confined worker on the arm's runtime starts from the item's pristine,
manifest-verified materials plus only the package's `analysis.py` and regular
files under `specs/`. It runs `python analysis.py`. The old answer and every
generated output stay outside; the comparison target never enters the worker.
A second replay on perturbed materials is diagnostic only. Matching outputs
require a separate source/provenance review before they count toward R; a
single insensitive perturbation does not establish that an answer was static.

Mechanical outcomes, one per launched trial: replayed, mismatch, failed, missing,
no_answer, infrastructure.

    python evaluation/pilot/replay.py RECORD_DIR ITEMS_DIR RUNTIME_ROOT
"""

import hashlib
import json
import math
import os
from pathlib import Path
import shutil
import stat
import sys
import tempfile

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
from evaluation.execution.worker import BoundaryError, Worker  # noqa: E402
from evaluation.pilot.launch import UV_PYTHON, verify_materials  # noqa: E402
from evaluation.revised.score import _reject_constant, validate_answer  # noqa: E402

TIMEOUT = 120
MAX_ANSWER_BYTES = 1_048_576
MAX_PACKAGE_FILE_BYTES = 5_000_000


class InvalidPackage(ValueError):
    pass


def read_regular(path, limit):
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(descriptor, "rb") as stream:
        info = os.fstat(stream.fileno())
        if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
            raise ValueError("Artifact must be a regular file without shared hardlinks")
        if info.st_size > limit:
            raise ValueError("Artifact exceeds the byte limit")
        data = stream.read(limit + 1)
    if len(data) > limit:
        raise ValueError("Artifact exceeds the byte limit")
    return data


def unique_object(pairs):
    value = {}
    for key, item in pairs:
        if key in value:
            raise ValueError("Duplicate JSON object key")
        value[key] = item
    return value


def load(path):
    try:
        data = read_regular(path, MAX_ANSWER_BYTES)
        value = json.loads(data, parse_constant=_reject_constant, object_pairs_hook=unique_object)
        answer, error = validate_answer(value)
    except (OSError, UnicodeDecodeError, ValueError, RecursionError) as exc:
        return None, str(exc), None
    return answer, error, hashlib.sha256(data).hexdigest()


def package_files(workspace):
    """analysis.py and regular files under specs/, never following links."""
    workspace = Path(workspace)
    files = []
    script = workspace / "analysis.py"
    if script.is_symlink() or not script.is_file():
        return None
    files.append(Path("analysis.py"))
    specs = workspace / "specs"
    if specs.is_dir() and not specs.is_symlink():
        for parent, folders, names in os.walk(specs, followlinks=False):
            folders[:] = [f for f in folders if not (Path(parent) / f).is_symlink()]
            for name in names:
                path = Path(parent) / name
                if stat.S_ISREG(path.lstat().st_mode):
                    files.append(path.relative_to(workspace))
    return files


def perturb(path, perturbation):
    """Apply the item's frozen perturbation to one materials file in place."""
    lines = path.read_text().splitlines(keepends=True)
    kind, match, value = perturbation["kind"], perturbation["match"], perturbation["value"]
    if kind == "add_row":
        out = []
        for line in lines:
            sep = "\t" if "\t" in line else ("," if "," in line else None)
            cells = line.rstrip("\n").split(sep)
            if cells and cells[0].strip() == match:
                cells = [cells[0]] + [str(int(c) + value) if c.strip().lstrip("-").isdigit() else c for c in cells[1:]]
                line = (sep or " ").join(cells) + "\n"
            out.append(line)
        path.write_text("".join(out))
    elif kind == "scale_column":
        header = lines[0].rstrip("\n").split(",")
        column = header.index(match)
        out = [lines[0]]
        for line in lines[1:]:
            cells = line.rstrip("\n").split(",")
            try:
                cells[column] = repr(round(float(cells[column]) * value, 6))
            except (ValueError, IndexError):
                pass
            out.append(",".join(cells) + "\n")
        path.write_text("".join(out))
    else:
        raise ValueError(f"unknown perturbation {kind}")


def execute(materials, workspace, files, runtime, scratch, perturbation=None, evidence=None):
    trial = scratch / "trial"
    trial.mkdir(parents=True)
    for source in materials:
        shutil.copyfile(source, trial / source.name)
    if perturbation:
        perturb(trial / perturbation["file"], perturbation)
    for relative in files:
        (trial / relative).parent.mkdir(parents=True, exist_ok=True)
        try:
            data = read_regular(workspace / relative, MAX_PACKAGE_FILE_BYTES)
        except (OSError, ValueError) as exc:
            raise InvalidPackage(str(exc)) from exc
        (trial / relative).write_bytes(data)
    evidence = evidence or scratch / "evidence"
    evidence.mkdir(parents=True, exist_ok=False)
    hashes = {p.relative_to(trial).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
              for p in sorted(trial.rglob("*")) if p.is_file()}
    (evidence / "staged-sha256.json").write_text(json.dumps(hashes, indent=2) + "\n")
    worker = Worker(trial, runtime, runtime / "bin/python", evidence / "audit", trusted_read_roots=[UV_PYTHON],
                    timeout_seconds=TIMEOUT, max_output_bytes=65536)
    result = worker.run_python(["analysis.py"], request={"tool": "replay"})
    answer, error, digest = load(trial / "answer.json")
    result = result | {"answer_error": error, "answer_sha256": digest}
    (evidence / "execution.json").write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    if answer is not None:
        (evidence / "answer.json").write_text(json.dumps(answer, indent=2, allow_nan=False) + "\n")
    return result, answer


def has_numbers(value):
    if isinstance(value, dict):
        return any(has_numbers(v) for v in value.values())
    if isinstance(value, list):
        return any(has_numbers(v) for v in value)
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def agree(a, b, tolerance, integers=(), path=""):
    if isinstance(a, dict):
        return isinstance(b, dict) and a.keys() == b.keys() and all(
            agree(a[k], b[k], tolerance, integers, f"{path}.{k}" if path else k) for k in a)
    if isinstance(a, list):
        return isinstance(b, list) and len(a) == len(b) and all(
            agree(x, y, tolerance, integers, f"{path}[{i}]") for i, (x, y) in enumerate(zip(a, b)))
    if isinstance(a, (int, float)) and not isinstance(a, bool):
        return isinstance(b, (int, float)) and not isinstance(b, bool) and (
            a == b if path in integers else math.isclose(a, b, rel_tol=tolerance["rel"], abs_tol=tolerance["abs"]))
    return type(a) is type(b) and a == b


def execution_summary(result):
    return {k: result.get(k) for k in ("status", "exit_code", "code", "answer_error")} | {
        "stderr_tail": (result.get("stderr") or "")[-800:]}


def evaluate(record, items_dir, runtime_root, evidence):
    record = Path(record)
    trial = json.loads((record / "trial.json").read_text())["trial"]
    item_dir = Path(items_dir) / trial["item"]
    key = json.loads((item_dir / "key.json").read_text())
    workspace = record / "workspace"
    out = {"trial": trial["trial_id"], "item": trial["item"], "arm": trial["arm"]}
    original, error, digest = load(workspace / "answer.json")
    out["original_answer_sha256"] = digest
    if original is None:
        return out | {"outcome": "no_answer", "answer_error": error}
    files = package_files(workspace)
    if files is None:
        return out | {"outcome": "missing"}
    out["files"] = [f.as_posix() for f in files]
    runtime = Path(runtime_root) / trial["arm"]
    try:
        materials = verify_materials(items_dir, trial["item"])
        with tempfile.TemporaryDirectory(prefix="replay-") as scratch:
            result, regenerated = execute(materials, workspace, files, runtime, Path(scratch) / "a",
                                          evidence=evidence / "pristine")
            perturbed = None
            perturbed_result = None
            if result.get("status") == "ok" and regenerated is not None and has_numbers(regenerated["results"]) and key.get("replay_perturbation"):
                perturbed_result, perturbed = execute(materials, workspace, files, runtime, Path(scratch) / "b",
                                                      key["replay_perturbation"], evidence=evidence / "perturbed")
    except InvalidPackage as exc:
        return out | {"outcome": "failed", "package_error": str(exc)}
    except (BoundaryError, OSError, ValueError) as exc:
        return out | {"outcome": "infrastructure", "error": f"{type(exc).__name__}: {exc}"}
    if result.get("code") == "execution_failed":
        return out | {"outcome": "infrastructure", "error": result.get("message")}
    out["execution"] = execution_summary(result)
    if perturbed_result is not None:
        out["perturbation_execution"] = execution_summary(perturbed_result)
        if perturbed_result.get("code") == "execution_failed":
            return out | {"outcome": "infrastructure", "error": perturbed_result.get("message")}
    if result.get("status") != "ok" or regenerated is None:
        return out | {"outcome": "failed"}
    tolerance = key["tolerance"]
    claims_match = {k: v for k, v in original.items() if k != "results"} == {
        k: v for k, v in regenerated.items() if k != "results"}
    results_match = agree(original["results"], regenerated["results"], tolerance, key.get("integer_results", ()))
    if not claims_match or not results_match:
        return out | {"outcome": "mismatch", "claims_match": claims_match, "results_match": results_match}
    out["provenance_review_required"] = True
    if not has_numbers(original["results"]):
        return out | {"outcome": "replayed", "numeric": "not_applicable", "perturbation": "not_applicable"}
    if perturbed_result is None:
        out["perturbation"] = "not_configured"
    elif perturbed_result.get("status") != "ok" or perturbed is None:
        out["perturbation"] = "failed"
    else:
        out["perturbation"] = "unchanged" if agree(regenerated["results"], perturbed["results"], tolerance,
                                                  key.get("integer_results", ())) else "changed"
    return out | {"outcome": "replayed"}


def replay(record, items_dir, runtime_root):
    record = Path(record)
    evidence_root = record / "replay"
    evidence_root.mkdir(exist_ok=True)
    evidence = Path(tempfile.mkdtemp(prefix="attempt-", dir=evidence_root))
    result = evaluate(record, items_dir, runtime_root, evidence)
    result["evidence_dir"] = str(evidence)
    result["replay_source_sha256"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    (evidence / "receipt.json").write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    return result


if __name__ == "__main__":
    print(json.dumps(replay(*sys.argv[1:4]), indent=1))
