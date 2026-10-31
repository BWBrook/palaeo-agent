"""Separate sprint-2 controller using the unchanged sprint-1 trial runner."""

import argparse
import hashlib
import importlib.util
import json
import os
import random
import re
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
ROOT = Path.home() / "palaeo-eval/sprint2"
RUNTIME = Path.home() / "palaeo-eval/sprint2-runtime"
SMOKE = HERE / "smoke/codex-v1"
FREEZE = HERE / "FREEZE.json"
VERSION = "sprint2-group-smoke-v1"
ITEMS = tuple(f"G{n}-{variant}" for n in (1, 2, 3) for variant in ("trap", "twin"))
SEED = 20261031
sys.path.insert(0, str(REPO / "evaluation/harness"))
import trial

trial.ROOT = ROOT
trial.RUNTIME = RUNTIME


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n")


def git(*args):
    return subprocess.run(["git", *args], cwd=REPO, capture_output=True, text=True, check=True).stdout.strip()


def source_commit(value):
    commit = git("rev-parse", f"{value}^{{commit}}")
    git("diff", "--exit-code", commit, "--", "src", "pyproject.toml", "uv.lock")
    if git("ls-files", "--others", "--exclude-standard", "--", "src", "pyproject.toml", "uv.lock"):
        raise RuntimeError("untracked implementation files are not part of the pinned commit")
    return commit


def source_files():
    paths = [REPO / name for name in (
        "pyproject.toml", "uv.lock", "docs/permanova-contract.md", "docs/sprints-1-2.md",
        "tests/test_sprint2_items.py", "evaluation/score.py", "evaluation/SCORING.md",
        "evaluation/answer.schema.json", "evaluation/items/MANIFEST.json", "evaluation/runtime/requirements.txt")]
    paths += sorted((REPO / "src").rglob("*.py"))
    paths += [p for p in sorted((REPO / "evaluation/harness").iterdir()) if p.suffix in {".py", ".md"}]
    paths += [p for p in sorted(HERE.iterdir()) if p.suffix in {".py", ".md"}]
    paths += [p for p in sorted((HERE / "items").rglob("*")) if p.is_file()]
    paths += [HERE / "preflight/canary-outside.txt"]
    return {str(p.relative_to(REPO)): sha(p) for p in sorted(set(paths))}


def verify_runtime():
    record = json.loads((RUNTIME / "runtime.json").read_text())
    if record["arms"]["direct"]["palaeo_agent_importable"] or not record["arms"]["toolkit"]["palaeo_agent_importable"]:
        raise RuntimeError("runtime arm imports do not match the design")
    direct = record["arms"]["direct"]["freeze"]
    toolkit = [line for line in record["arms"]["toolkit"]["freeze"]
               if line.split(" @ ", 1)[0].split("==", 1)[0].lower().replace("_", "-") != "palaeo-agent"]
    if direct != toolkit:
        raise RuntimeError("non-toolkit dependencies differ between arms")
    wheel = RUNTIME / "wheel" / record["wheel"]
    if sha(wheel) != record["wheel_sha256"] or sha(RUNTIME / "palaeo_agent_discover.json") != record["discover_sha256"]:
        raise RuntimeError("runtime wheel or discovery hash changed")
    return record


def build_runtime(commit):
    commit = source_commit(commit)
    if RUNTIME.exists():
        raise RuntimeError("refusing to replace an existing sprint-2 runtime")
    spec = importlib.util.spec_from_file_location("sprint2_runtime_builder", REPO / "evaluation/harness/runtime.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    record = module.build(RUNTIME, RUNTIME / "wheel")
    record["source_commit"] = commit
    save(RUNTIME / "runtime.json", record)
    verify_runtime()
    save(HERE / "artifacts/runtime.json", record)
    return {"source_commit": commit, "wheel_sha256": record["wheel_sha256"], "runtime": str(RUNTIME)}


def freeze(commit):
    if FREEZE.exists():
        raise RuntimeError("freeze already exists; amendments require a new instrument version")
    commit = source_commit(commit)
    runtime = verify_runtime()
    if runtime.get("source_commit") != commit:
        raise RuntimeError("runtime is not from the pinned implementation commit")
    manifest = json.loads((HERE / "items/MANIFEST.json").read_text())
    if manifest["items"] != sorted(ITEMS):
        raise RuntimeError("exactly the six declared items are required")
    value = {
        "version": VERSION, "bank_version": manifest["version"], "scorer_version": "sprint2-group-score-v1",
        "source_commit": commit, "files": source_files(), "runtime_manifest_sha256": sha(RUNTIME / "runtime.json"),
        "wheel_sha256": runtime["wheel_sha256"], "discovery_sha256": runtime["discover_sha256"],
        "runtime": str(RUNTIME), "original_scorer_sha256": sha(REPO / "evaluation/score.py"),
    }
    save(FREEZE, value)
    return value


def verify_freeze():
    frozen = json.loads(FREEZE.read_text())
    if frozen["version"] != VERSION or frozen["files"] != source_files():
        raise RuntimeError("the frozen source, instrument, bank or original harness has changed")
    source_commit(frozen["source_commit"])
    verify_runtime()
    if sha(RUNTIME / "runtime.json") != frozen["runtime_manifest_sha256"]:
        raise RuntimeError("runtime manifest changed after freeze")
    return frozen


def make_plan():
    frozen = verify_freeze()
    path = SMOKE / "plan.json"
    if path.exists():
        raise RuntimeError("plan already exists; no replacement of a frozen order")
    order = [(item, arm) for item in ITEMS for arm in ("direct", "toolkit")]
    random.Random(SEED).shuffle(order)
    plan = {
        "version": VERSION, "bank_version": frozen["bank_version"], "scorer_version": frozen["scorer_version"],
        "source_commit": frozen["source_commit"], "freeze_sha256": sha(FREEZE),
        "backend": "codex", "model": "gpt-6.1-sol", "effort": "medium", "wall_seconds": 300,
        "token_ceiling": 300000, "counted_tokens": trial.COUNTED["codex"], "seed": SEED,
        "retries": 0, "order": [{"item": item, "arm": arm} for item, arm in order],
    }
    save(path, plan)
    return plan


def validate_plan(plan):
    expected = {(item, arm) for item in ITEMS for arm in ("direct", "toolkit")}
    observed = [(step["item"], step["arm"]) for step in plan["order"]]
    if len(observed) != 12 or set(observed) != expected:
        raise RuntimeError("the plan must contain exactly twelve unique declared item-arm trials")
    for field, value in {"version": VERSION, "backend": "codex", "model": "gpt-6.1-sol", "effort": "medium",
                         "wall_seconds": 300, "token_ceiling": 300000, "retries": 0, "seed": SEED}.items():
        if plan.get(field) != value:
            raise RuntimeError(f"frozen plan setting changed: {field}")
    order = [(item, arm) for item in ITEMS for arm in ("direct", "toolkit")]
    random.Random(SEED).shuffle(order)
    if observed != order or plan["freeze_sha256"] != sha(FREEZE):
        raise RuntimeError("plan order or freeze hash changed")
    if trial.BACKENDS["codex"] != {"model": plan["model"], "effort": plan["effort"]}:
        raise RuntimeError("original runner backend configuration changed")


def preflight():
    frozen = verify_freeze()
    report_path = HERE / "preflight/report.json"
    if report_path.exists():
        raise RuntimeError("preflight record already exists; preserve failures rather than overwrite")
    neighbor = ROOT / "preflight-neighbor.txt"
    neighbor.parent.mkdir(parents=True, exist_ok=True)
    neighbor.write_text("sprint2-neighbor-canary\n")
    protected = {
        "outside_canary": HERE / "preflight/canary-outside.txt", "neighbor_trial": neighbor,
        "sprint2_key": HERE / "items/G1-trap/key.json",
        "sprint1_key": REPO / "evaluation/items/D3-trap/key.json", "checkout": REPO / "README.md",
        "source": REPO / "src/palaeo_agent/__init__.py", "agent_instructions": Path.home() / ".codex/AGENTS.md",
    }
    for path in protected.values():
        if not path.is_file():
            raise RuntimeError(f"preflight protected target does not exist: {path}")
    records = {}
    for arm in ("direct", "toolkit"):
        trial_root = ROOT / "preflight" / arm
        if trial_root.exists():
            raise RuntimeError("preflight workspace already exists")
        for name in ("ws", "home", "tmp"):
            (trial_root / name).mkdir(parents=True)
        targets = protected | {"other_arm_runtime": RUNTIME / ("toolkit" if arm == "direct" else "direct") / "pyvenv.cfg"}
        code = """import importlib.util, json, pathlib
targets = TARGETS
reads = {}
for name, filename in targets.items():
    try:
        pathlib.Path(filename).read_bytes()
        reads[name] = 'unexpected_allowed'
    except OSError as exc:
        reads[name] = 'denied' if exc.errno in (1,13) else 'other_error:' + str(exc.errno)
try:
    pathlib.Path(WRITE_TARGET).write_text('unexpected write')
    outside_write = 'unexpected_allowed'
except OSError as exc:
    outside_write = 'denied' if exc.errno in (1,13) else 'other_error:' + str(exc.errno)
import numpy, scipy, pandas, matplotlib, pydantic
spec = importlib.util.find_spec('palaeo_agent')
origin = str(pathlib.Path(spec.origin).resolve()) if spec else None
print(json.dumps({'reads': reads, 'outside_write': outside_write, 'toolkit_importable': spec is not None,
                 'toolkit_origin': origin, 'numpy': numpy.__version__, 'scipy': scipy.__version__,
                 'pandas': pandas.__version__, 'matplotlib': matplotlib.__version__, 'pydantic': pydantic.__version__}))
""".replace("TARGETS", repr({name: str(path) for name, path in targets.items()}))
        code = code.replace("WRITE_TARGET", repr(str(HERE / "preflight/denied-write.txt")))
        probe = trial_root / "ws/probe.py"
        probe.write_text(code)
        sandbox = trial.profile(backend="codex", trial_root=trial_root, runtime=RUNTIME / arm)
        (trial_root / "sandbox.sb").write_text(sandbox)
        env = {"PATH": f"{RUNTIME / arm / 'bin'}:/usr/bin:/bin", "HOME": str(trial_root / "home"),
               "TMPDIR": str(trial_root / "tmp"), "LANG": "en_AU.UTF-8", "USER": os.environ["USER"],
               "LOGNAME": os.environ["USER"], "VIRTUAL_ENV": str(RUNTIME / arm),
               "MPLCONFIGDIR": str(trial_root / "tmp/matplotlib")}
        proc = subprocess.run(["/usr/bin/sandbox-exec", "-f", str(trial_root / "sandbox.sb"),
                               str(RUNTIME / arm / "bin/python"), "-I", str(probe)], cwd=trial_root / "ws",
                              env=env, capture_output=True, text=True, timeout=60)
        (trial_root / "stdout.txt").write_text(proc.stdout)
        (trial_root / "stderr.txt").write_text(proc.stderr)
        try:
            observed = json.loads(proc.stdout)
        except json.JSONDecodeError:
            observed = {"error": "probe did not return JSON"}
        origin = observed.get("toolkit_origin")
        expected_import = arm == "toolkit"
        passed = (proc.returncode == 0 and observed.get("outside_write") == "denied"
                  and all(value == "denied" for value in observed.get("reads", {}).values())
                  and set(observed.get("reads", {})) == set(targets)
                  and observed.get("toolkit_importable") is expected_import
                  and (not expected_import or (origin and Path(origin).is_relative_to(RUNTIME / "toolkit")
                                               and "site-packages" in Path(origin).parts)))
        records[arm] = {"passed": bool(passed), "returncode": proc.returncode, **observed,
                        "sandbox_sha256": hashlib.sha256(sandbox.encode()).hexdigest()}
        dest = HERE / "preflight" / arm
        shutil.copytree(trial_root, dest)
        shutil.rmtree(trial_root)
    report = {"source_commit": frozen["source_commit"], "freeze_sha256": sha(FREEZE),
              "passed": all(record["passed"] for record in records.values()), "arms": records,
              "scope": "Controller sandbox syscall checks, not live model trials; network isolation not established."}
    save(report_path, report)
    if not report["passed"]:
        raise RuntimeError("preflight failed; failure records preserved")
    return report


LEAK_PATTERNS = {
    "development_checkout": r"/Users/[^/\s]+/work/",
    "agent_config": r"\.claude/|\.codex/", "key_or_generator": r"key\.json|build_items\.py|FREEZE\.json",
    "other_trial": r"palaeo-eval/sprint2/t/([a-f0-9]+)",
    "package_install": r"\bpip3? install\b|\buv (pip|add|tool)\b|\bconda install\b",
    "network_fetch": r"\bcurl\b|\bwget\b|https?://(?!json-schema\.org)",
    "blocked_access": r"Operation not permitted|Permission denied",
}


def leak_scan(record, trial_id):
    text = (record / "transcript.jsonl").read_text() + (record / "stderr.txt").read_text()
    hits = {}
    for name, pattern in LEAK_PATTERNS.items():
        found = list(re.finditer(pattern, text))
        if name == "other_trial":
            found = [match for match in found if match.group(1) != trial_id]
        if found:
            hits[name] = len(found)
    return hits


def require_committed(paths):
    relative = [str(path.relative_to(REPO)) for path in paths]
    git("ls-files", "--error-unmatch", "--", *relative)
    git("diff", "--exit-code", "HEAD", "--", *relative)


def run():
    verify_freeze()
    plan_path = SMOKE / "plan.json"
    plan = json.loads(plan_path.read_text())
    validate_plan(plan)
    report_path = HERE / "preflight/report.json"
    report = json.loads(report_path.read_text())
    if not report["passed"] or report["freeze_sha256"] != sha(FREEZE):
        raise RuntimeError("passing preflight for the frozen instrument is required")
    frozen = json.loads(FREEZE.read_text())
    require_committed([FREEZE, plan_path, report_path] + [REPO / path for path in frozen["files"]])
    SMOKE.mkdir(parents=True, exist_ok=True)
    lock = SMOKE / "controller.lock"
    fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    os.close(fd)
    spent, log = 0, []
    try:
        for n, step in enumerate(plan["order"], 1):
            verify_freeze()
            record = SMOKE / "trials" / f"{n:02d}-{step['item']}-{step['arm']}"
            if record.exists():
                if not (record / "trial.json").is_file():
                    raise RuntimeError("incomplete trial exists; no retry is permitted")
                meta = json.loads((record / "trial.json").read_text())
            elif spent >= plan["token_ceiling"]:
                log.append({"step": n, **step, "status": "not_run_token_ceiling"})
                save(SMOKE / "run_log.json", log)
                continue
            else:
                before = set((ROOT / "t").glob("*"))
                try:
                    meta = trial.run(HERE / "items" / step["item"] / "materials", step["arm"], "codex",
                                     record, plan["wall_seconds"])
                except Exception as exc:
                    save(record / "controller_error.json", {"error": type(exc).__name__, "detail": str(exc),
                                                           "step": n, **step, "retry_permitted": False})
                    raise
                finally:
                    for path in set((ROOT / "t").glob("*")) - before:
                        shutil.rmtree(path)
            scan = leak_scan(record, meta["trial_id"])
            save(record / "leak_scan.json", scan)
            spent += meta["counted_tokens"]
            log.append({"step": n, **step, "status": "run", "termination": meta["termination"],
                        "elapsed_seconds": meta["elapsed_seconds"], "counted_tokens": meta["counted_tokens"],
                        "cumulative_counted_tokens": spent, "leak_scan": scan})
            save(SMOKE / "run_log.json", log)
            print(json.dumps(log[-1]), flush=True)
    finally:
        lock.unlink()
    return log


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    for command in ("build-runtime", "freeze"):
        command_parser = sub.add_parser(command)
        command_parser.add_argument("source_commit")
    for command in ("plan", "preflight", "run"):
        sub.add_parser(command)
    args = parser.parse_args()
    result = {"build-runtime": lambda: build_runtime(args.source_commit), "freeze": lambda: freeze(args.source_commit),
              "plan": make_plan, "preflight": preflight, "run": run}[args.command]()
    if args.command != "run":
        print(json.dumps(result, indent=2))
