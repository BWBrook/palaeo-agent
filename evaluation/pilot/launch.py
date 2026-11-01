"""Pilot launcher, Claude route (docs/pilot-protocol.md, launch conditions).

Every trial: pinned client binary; a fake-endpoint inventory capture that must
equal the frozen inventory; Claude Code in --bare mode (no CLAUDE.md, memory,
hooks, plugins or keychain) with only the confined worker MCP server; the
client's init record checked against the inventory; tool events reconciled
with the worker audit log; a turn cap and a wall-clock kill; process cleanup
verified; usage required. Any breach halts further launches. A trial record,
once started, is never rerun.

    python evaluation/pilot/launch.py plan ITEMS_DIR PLAN.json --runtime RUNTIME_ROOT [...]
    python evaluation/pilot/launch.py run PLAN.json OUT_DIR --key-file FILE
"""

import argparse
import hashlib
import json
import os
from pathlib import Path
import random
import shutil
import signal
import subprocess
import sys
import tempfile
import threading
import time

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path.insert(0, str(REPO / "evaluation/sprint3/claude-client-boundary"))
sys.path.insert(0, str(REPO))
from probe import DUMMY, UV_PYTHON, endpoint  # noqa: E402
from evaluation.pilot.score import score  # noqa: E402

MODEL = "claude-sonnet-5-5"
PROMPTS = HERE / "prompts"


class Halt(RuntimeError):
    pass


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def client_path():
    return Path(shutil.which("claude")).resolve()


def prompt(arm):
    text = (PROMPTS / "analyst.md").read_text()
    return text + (PROMPTS / "analyst-toolkit.md").read_text() if arm == "toolkit" else text


def stage(trial_root, materials, runtime_root, arm, audit_dir):
    trial_root.mkdir(parents=True)
    for source in sorted(Path(materials).iterdir()):
        shutil.copyfile(source, trial_root / source.name)
    runtime = Path(runtime_root) / arm
    worker = {"trial_root": str(trial_root), "runtime": str(runtime), "python": str(runtime / "bin/python"),
              "log_dir": str(audit_dir), "trusted_read_roots": [str(UV_PYTHON)], "timeout_seconds": 60,
              "max_output_bytes": 65536, "toolkit": arm == "toolkit"}
    config = trial_root.parent / "worker.json"
    config.write_text(json.dumps(worker))
    mcp = trial_root.parent / "mcp.json"
    mcp.write_text(json.dumps({"mcpServers": {"worker": {
        "type": "stdio", "command": str(REPO / ".venv/bin/python"),
        "args": ["-m", "evaluation.execution.server", "--config", str(config)],
        "cwd": str(REPO), "env": {"PYTHONPATH": str(REPO)}}}}))
    return mcp


def command(client, text, mcp, max_turns, model):
    return [str(client), "--bare", "-p", text, "--tools=", "--strict-mcp-config", "--mcp-config", str(mcp),
            "--setting-sources=", "--no-session-persistence", "--permission-mode", "bypassPermissions",
            "--allowedTools", "mcp__worker__*", "--model", model, "--max-turns", str(max_turns),
            "--output-format", "stream-json", "--verbose"]


def environment(home, key, base_url=None):
    env = {"PATH": "/usr/bin:/bin:/opt/homebrew/bin", "HOME": str(home), "USER": os.environ["USER"],
           "LOGNAME": os.environ["USER"], "ANTHROPIC_API_KEY": key, "DISABLE_TELEMETRY": "1",
           "DISABLE_ERROR_REPORTING": "1", "CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC": "1"}
    if base_url:
        env["ANTHROPIC_BASE_URL"] = base_url
    return env


def capture_inventory(runtime_root, arm, model):
    """Offline: the tools the identical command advertises, from a fake endpoint."""
    with tempfile.TemporaryDirectory() as scratch:
        scratch = Path(scratch)
        materials = scratch / "materials"
        materials.mkdir()
        (materials / "task.md").write_text("inventory capture\n")
        mcp = stage(scratch / "work/trial", materials, runtime_root, arm, scratch / "audit")
        (scratch / "home").mkdir()
        log = []
        server = endpoint([], log)
        try:
            subprocess.run(command(client_path(), prompt(arm), mcp, 2, model), cwd=scratch / "home",
                           env=environment(scratch / "home", DUMMY, f"http://127.0.0.1:{server.server_address[1]}"),
                           stdin=subprocess.DEVNULL, capture_output=True, timeout=120)
        finally:
            server.shutdown()
        if not log:
            raise Halt("inventory capture produced no request")
        return sorted(log[0]["tools"])


def cleanup(marker):
    """Kill and verify the absence of any process whose arguments name this trial."""
    def survivors():
        found = subprocess.run(["pgrep", "-f", marker], capture_output=True, text=True).stdout.split()
        return [int(pid) for pid in found if int(pid) != os.getpid()]
    for pid in survivors():
        try:
            os.kill(pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
    time.sleep(0.2)
    left = survivors()
    if left:
        raise Halt(f"processes survived cleanup: {left}")


def reconcile(events, audit_dir, inventory):
    uses = {}
    results = {}
    for event in events:
        for block in (event.get("message") or {}).get("content", []) if isinstance(event.get("message"), dict) else []:
            if not isinstance(block, dict):
                continue
            if block.get("type") == "tool_use":
                uses[block["id"]] = block["name"]
            elif block.get("type") == "tool_result":
                results[block["tool_use_id"]] = block
    calls = [json.loads(line) for line in (Path(audit_dir) / "calls.jsonl").read_text().splitlines()] \
        if (Path(audit_dir) / "calls.jsonl").exists() else []
    worker_calls = [c for c in calls if c["request"].get("tool") != "supervisor_load_tool_definitions"]
    categories = {"worker": 0, "client_refusal": 0, "other": []}
    for use_id, name in uses.items():
        result = results.get(use_id, {})
        text = json.dumps(result.get("content"))
        if name in inventory and name.startswith("mcp__worker__"):
            categories["worker"] += 1
        elif name not in inventory and result.get("is_error") and "No such tool available" in text:
            categories["client_refusal"] += 1
        else:
            categories["other"].append({"id": use_id, "name": name})
    categories["worker_audit_calls"] = len(worker_calls)
    categories["consistent"] = not categories["other"] and categories["worker"] == len(worker_calls)
    return categories


def run_trial(trial, plan, out_dir, key, base_url=None):
    record = Path(out_dir) / "trials" / trial["trial_id"]
    record.mkdir(parents=True, exist_ok=False)
    started = {"trial": trial, "started_unix": time.time()}
    (record / "started.json").write_text(json.dumps(started) + "\n")
    if sha(client_path()) != plan["client_sha256"]:
        raise Halt("client binary differs from the plan")
    inventory = capture_inventory(plan["runtime_root"], trial["arm"], plan["model"])
    if inventory != plan["inventory"][trial["arm"]]:
        raise Halt(f"captured inventory differs: {inventory}")
    work = Path(tempfile.mkdtemp(prefix="pilot-", dir=plan["work_root"]))
    trial_root = work / "trial"
    audit = record / "worker-audit"
    mcp = stage(trial_root, Path(plan["items_dir"]) / trial["item"] / "materials", plan["runtime_root"], trial["arm"], audit)
    (work / "home").mkdir()
    proc = subprocess.Popen(command(client_path(), prompt(trial["arm"]), mcp, plan["max_turns"], plan["model"]),
                            cwd=work / "home", env=environment(work / "home", key, base_url),
                            stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            start_new_session=True, text=True)
    events, breach = [], []

    def read():
        for line in proc.stdout:
            try:
                event = json.loads(line)
            except ValueError:
                continue
            events.append(event)
            if event.get("type") == "system" and event.get("subtype") == "init" and \
                    sorted(event.get("tools", [])) != sorted(t for t in plan["inventory"][trial["arm"]]
                                                             if t != "DeferredToolPlaceholder"):
                breach.append("init_inventory")
                os.killpg(proc.pid, signal.SIGKILL)

    reader = threading.Thread(target=read, daemon=True)
    reader.start()
    termination = "exited"
    try:
        proc.wait(timeout=plan["wall_seconds"])
    except subprocess.TimeoutExpired:
        termination = "wall_limit"
        os.killpg(proc.pid, signal.SIGKILL)
        proc.wait()
    reader.join(timeout=5)
    try:
        os.killpg(proc.pid, signal.SIGKILL)
    except ProcessLookupError:
        pass
    cleanup(str(trial_root))
    (record / "transcript.jsonl").write_text("".join(json.dumps(e) + "\n" for e in events))
    (record / "stderr.txt").write_text(proc.stderr.read())
    result = next((e for e in reversed(events) if e.get("type") == "result"), None)
    usage = (result or {}).get("usage")
    counted = None if not usage else sum(usage.get(k, 0) or 0 for k in
                                        ("input_tokens", "cache_creation_input_tokens", "output_tokens"))
    categories = reconcile(events, audit, plan["inventory"][trial["arm"]])
    shutil.copytree(trial_root, record / "workspace", ignore=shutil.ignore_patterns(".worker"))
    outcome = score(record / "workspace", Path(plan["items_dir"]) / trial["item"],
                    "wall_limit" if termination == "wall_limit" else "exited")
    summary = {**started, "termination": termination, "exit_code": proc.returncode, "breach": breach,
               "result_subtype": (result or {}).get("subtype"), "usage": usage, "counted_tokens": counted,
               "cache_read_tokens": (usage or {}).get("cache_read_input_tokens"), "reconciliation": categories,
               "score": outcome, "finished_unix": time.time()}
    (record / "trial.json").write_text(json.dumps(summary, indent=1) + "\n")
    shutil.rmtree(work)
    if breach or not categories["consistent"]:
        raise Halt(f"boundary breach or unreconciled tool events in {trial['trial_id']}")
    if counted is None:
        raise Halt(f"usage unavailable in {trial['trial_id']}")
    return summary


def make_plan(items_dir, path, *, runtime_root, work_root, ceiling, sessions=2, seed=20261101, max_turns=60,
              wall_seconds=600, model=MODEL, families=None):
    items_dir = Path(items_dir).resolve()
    keys = {p.parent.name: json.loads(p.read_text()) for p in sorted(items_dir.glob("*/key.json"))}
    families = families or sorted({k["family"] for k in keys.values()})
    rng = random.Random(seed)
    blocks = []
    for family in families:
        for session in range(1, sessions + 1):
            block = [{"item": item, "arm": arm, "session": session, "family": family}
                     for item, k in keys.items() if k["family"] == family for arm in ("direct", "toolkit")]
            rng.shuffle(block)
            blocks.append(block)
    rng.shuffle(blocks)
    trials = []
    for b, block in enumerate(blocks):
        for t in block:
            trials.append(dict(t, trial_id=f"T{len(trials) + 1:03d}", block=b + 1))
    plan = {"model": model, "client": str(client_path()), "client_sha256": sha(client_path()),
            "runtime_root": str(Path(runtime_root).resolve()),
            "runtime_manifest_sha256": sha(Path(runtime_root) / "runtime.json"),
            "items_dir": str(items_dir), "items_manifest_sha256": sha(items_dir / "MANIFEST.json"),
            "prompts_sha256": {p.name: sha(p) for p in sorted(PROMPTS.glob("*.md"))},
            "inventory": {arm: capture_inventory(runtime_root, arm, model) for arm in ("direct", "toolkit")},
            "work_root": str(Path(work_root).resolve()), "max_turns": max_turns, "wall_seconds": wall_seconds,
            "counted_token_ceiling": ceiling, "seed": seed, "trials": trials}
    with Path(path).open("x") as stream:
        stream.write(json.dumps(plan, indent=1) + "\n")
    return plan


def run(plan_path, out_dir, key, base_url=None):
    plan = json.loads(Path(plan_path).read_text())
    out_dir = Path(out_dir)
    (out_dir / "trials").mkdir(parents=True, exist_ok=True)
    spent = sum(json.loads(p.read_text()).get("counted_tokens") or 0 for p in (out_dir / "trials").glob("*/trial.json"))
    log = []
    for trial in plan["trials"]:
        if (out_dir / "trials" / trial["trial_id"]).exists():
            continue
        if spent >= plan["counted_token_ceiling"]:
            log.append({"stop": "ceiling", "spent": spent})
            break
        try:
            summary = run_trial(trial, plan, out_dir, key, base_url)
        except Halt as exc:
            log.append({"halt": str(exc), "trial": trial["trial_id"]})
            break
        spent += summary["counted_tokens"]
        log.append({"trial": trial["trial_id"], "outcome": summary["score"]["outcome"], "counted": summary["counted_tokens"]})
    with (out_dir / "run_log.jsonl").open("a") as stream:
        for entry in log:
            stream.write(json.dumps(entry) + "\n")
    return log


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    commands = parser.add_subparsers(dest="command", required=True)
    p = commands.add_parser("plan")
    p.add_argument("items_dir")
    p.add_argument("plan")
    p.add_argument("--runtime", required=True)
    p.add_argument("--work-root", required=True)
    p.add_argument("--ceiling", type=int, required=True)
    p.add_argument("--sessions", type=int, default=2)
    r = commands.add_parser("run")
    r.add_argument("plan")
    r.add_argument("out_dir")
    r.add_argument("--key-file", required=True, help="File holding the Anthropic API key; never recorded")
    args = parser.parse_args()
    if args.command == "plan":
        plan = make_plan(args.items_dir, args.plan, runtime_root=args.runtime, work_root=args.work_root,
                         ceiling=args.ceiling, sessions=args.sessions)
        print(json.dumps({"trials": len(plan["trials"]), "inventory": plan["inventory"]}))
    else:
        key = Path(args.key_file).read_text().strip()
        print(json.dumps(run(args.plan, args.out_dir, key)))


if __name__ == "__main__":
    main()
