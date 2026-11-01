"""End-to-end replay of an analyst package (docs/sprints-5-6-proposal.md, 5.1). No model is involved.

A fresh confined worker on the arm's runtime starts from the item's pristine,
manifest-verified materials plus only the package's `analysis.py` and regular
files under `specs/`. It runs `python analysis.py`. The old answer and every
generated output stay outside; the comparison target never enters the worker.
A second replay runs on materials with the item's frozen perturbation applied;
a package whose numbers do not move is `static`.

Outcomes, one per launched trial: replayed, static, mismatch, failed, missing,
no_answer, infrastructure.

    python evaluation/pilot/replay.py RECORD_DIR ITEMS_DIR RUNTIME_ROOT
"""

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

TIMEOUT = 120


def load(path):
    try:
        value = json.loads(Path(path).read_text())
    except (OSError, ValueError):
        return None
    return value if isinstance(value, dict) else None


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


def execute(materials, workspace, files, runtime, scratch, perturbation=None):
    trial = scratch / "trial"
    trial.mkdir(parents=True)
    for source in materials:
        shutil.copyfile(source, trial / source.name)
    if perturbation:
        perturb(trial / perturbation["file"], perturbation)
    for relative in files:
        (trial / relative).parent.mkdir(parents=True, exist_ok=True)
        descriptor = os.open(workspace / relative, os.O_RDONLY | os.O_NOFOLLOW)
        with os.fdopen(descriptor, "rb") as stream:
            (trial / relative).write_bytes(stream.read())
    worker = Worker(trial, runtime, runtime / "bin/python", scratch / "audit", trusted_read_roots=[UV_PYTHON],
                    timeout_seconds=TIMEOUT, max_output_bytes=65536)
    result = worker.run_python(["analysis.py"], request={"tool": "replay"})
    return result, load(trial / "answer.json")


def numbers(answer):
    return {k: v for k, v in (answer.get("results") or {}).items()
            if isinstance(v, (int, float)) and not isinstance(v, bool)}


def agree(a, b, tolerance):
    if a.keys() != b.keys():
        return False
    return all(math.isclose(a[k], b[k], rel_tol=tolerance["rel"], abs_tol=tolerance["abs"]) for k in a)


def replay(record, items_dir, runtime_root):
    record = Path(record)
    trial = json.loads((record / "trial.json").read_text())["trial"]
    item_dir = Path(items_dir) / trial["item"]
    key = json.loads((item_dir / "key.json").read_text())
    workspace = record / "workspace"
    out = {"trial": trial["trial_id"], "item": trial["item"], "arm": trial["arm"]}
    original = load(workspace / "answer.json")
    if original is None:
        return out | {"outcome": "no_answer"}
    files = package_files(workspace)
    if files is None:
        return out | {"outcome": "missing"}
    out["files"] = [f.as_posix() for f in files]
    runtime = Path(runtime_root) / trial["arm"]
    try:
        materials = verify_materials(items_dir, trial["item"])
        with tempfile.TemporaryDirectory(prefix="replay-") as scratch:
            result, regenerated = execute(materials, workspace, files, runtime, Path(scratch) / "a")
            perturbed = None
            if result.get("status") == "ok" and regenerated is not None and numbers(regenerated):
                perturbed_result, perturbed = execute(materials, workspace, files, runtime, Path(scratch) / "b",
                                                      key["replay_perturbation"])
    except (BoundaryError, OSError) as exc:
        return out | {"outcome": "infrastructure", "error": f"{type(exc).__name__}: {exc}"}
    if result.get("code") == "execution_failed":
        return out | {"outcome": "infrastructure", "error": result.get("message")}
    out["execution"] = {k: result.get(k) for k in ("status", "exit_code")} | {"stderr_tail": (result.get("stderr") or "")[-800:]}
    if result.get("status") != "ok" or regenerated is None:
        return out | {"outcome": "failed"}
    tolerance = key["tolerance"]
    if regenerated.get("status") != original.get("status") or not agree(numbers(original), numbers(regenerated), tolerance):
        return out | {"outcome": "mismatch", "original": numbers(original), "regenerated": numbers(regenerated)}
    if not numbers(original):
        return out | {"outcome": "replayed", "numeric": "not_applicable"}
    if perturbed is not None and numbers(perturbed) == numbers(regenerated):
        return out | {"outcome": "static"}
    if perturbed is None:
        out["perturbation"] = "perturbed replay produced no answer"
    return out | {"outcome": "replayed"}


if __name__ == "__main__":
    print(json.dumps(replay(*sys.argv[1:4]), indent=1))
