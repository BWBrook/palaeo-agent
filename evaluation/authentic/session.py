"""Authentic-workflow sessions (docs/research-workflow-next-step.md): one open research brief per session.

Reuses the pilot launcher's safeguards unchanged: frozen fingerprints, configuration-directory checks,
subscription login in the launch environment, captured tool inventory, init-record check, worker
reconciliation, process-group termination and link-refusing export. What differs from a pilot trial:

- materials come from `cases/<case>/materials`, verified against `cases/MANIFEST.json`;
- the prompt is `contract.md` (+ `toolkit.md` when the toolkit is offered) and the case brief;
- nothing is scored; the deliverable is replayed: `analysis.py` (+ `specs/`) runs in a fresh confined
  worker from pristine materials and its `results.json` must match the delivered one;
- after the session, one neutral retrospective question is asked by resuming it with no tools.

    python evaluation/authentic/session.py plan PLAN.json --runtime R --work-root W --config-dir C \
        --capture-config-dir CC --ceiling N --session ID:CASE:ARM ...
    python evaluation/authentic/session.py run PLAN.json OUT_DIR
"""

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import tempfile
import threading
import time
import os

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1]))
from evaluation.execution.worker import BoundaryError, Worker  # noqa: E402
from evaluation.pilot import launch  # noqa: E402
from evaluation.pilot.launch import (Halt, UV_PYTHON, USAGE_FIELDS, capture_inventory, client_path,  # noqa: E402
                                     complete_usage, environment, export, fingerprints, reconcile, stage,
                                     subscription_status, supervisor_home, no_instruction_ancestors, terminate,
                                     verify_config_dir, verify_materials, sha)
from evaluation.pilot.replay import MAX_PACKAGE_FILE_BYTES, agree, package_files, read_regular  # noqa: E402

CASES = HERE / "cases"
TOLERANCE = {"rel": 1e-6, "abs": 1e-9}
REPLAY_TIMEOUT = 300
SOURCE = ["evaluation/authentic/session.py", "evaluation/authentic/contract.md", "evaluation/authentic/toolkit.md",
          "evaluation/authentic/retrospective.md"]


def session_prompt(case, arm):
    text = (HERE / "contract.md").read_text()
    if arm == "toolkit":
        text += (HERE / "toolkit.md").read_text()
    return text + "\n## Brief\n\n" + (CASES / case / "brief.md").read_text()


def main_command(text, mcp, max_turns, model):
    """The pilot command, with session persistence kept so the retrospective can resume it."""
    return [a for a in launch.command(text, mcp, max_turns, model) if a != "--no-session-persistence"]


def retrospective_command(session_id, mcp, model):
    """Same tool definitions as the session (its history refers to them), but none is permitted."""
    return [str(client_path()), "-p", (HERE / "retrospective.md").read_text(), "--resume", session_id,
            "--tools=", "--strict-mcp-config", "--mcp-config", str(mcp), "--setting-sources=",
            "--model", model, "--max-turns", "1", "--output-format", "stream-json", "--verbose"]


def retrospective_mcp(work):
    """The session's worker server, logging to a separate audit directory."""
    config = json.loads((work / "worker.json").read_text())
    config["log_dir"] = str(Path(config["log_dir"]).parent / "retrospective-audit")
    (work / "worker-retrospective.json").write_text(json.dumps(config))
    mcp = json.loads((work / "mcp.json").read_text())
    mcp["mcpServers"]["worker"]["args"][-1] = str(work / "worker-retrospective.json")
    (work / "mcp-retrospective.json").write_text(json.dumps(mcp))
    return work / "mcp-retrospective.json", Path(config["log_dir"])


def stream(proc, events, on_event=None):
    def read():
        for line in proc.stdout:
            try:
                event = json.loads(line)
            except ValueError:
                continue
            events.append(event)
            if on_event:
                on_event(event)
    reader = threading.Thread(target=read, daemon=True)
    reader.start()
    return reader


def load_results(path):
    try:
        data = read_regular(path, MAX_PACKAGE_FILE_BYTES)
        return json.loads(data), hashlib.sha256(data).hexdigest(), None
    except (OSError, ValueError, UnicodeDecodeError) as exc:
        return None, None, f"{type(exc).__name__}: {exc}"


def replay(record, cases_dir, case, runtime):
    """Rerun the delivered analysis from pristine materials; compare results.json."""
    workspace = record / "workspace"
    out = {}
    original, digest, error = load_results(workspace / "results.json")
    out["original_results_sha256"] = digest
    if original is None:
        return out | {"outcome": "no_results", "error": error}
    files = package_files(workspace)
    if files is None:
        return out | {"outcome": "missing"}
    out["files"] = [f.as_posix() for f in files]
    evidence = Path(tempfile.mkdtemp(prefix="attempt-", dir=(record / "replay").resolve()))
    with tempfile.TemporaryDirectory(prefix="replay-") as scratch:
        trial = Path(scratch) / "trial"
        trial.mkdir()
        for source in verify_materials(cases_dir, case):
            shutil.copyfile(source, trial / source.name)
        for relative in files:
            (trial / relative).parent.mkdir(parents=True, exist_ok=True)
            (trial / relative).write_bytes(read_regular(workspace / relative, MAX_PACKAGE_FILE_BYTES))
        staged = {p.relative_to(trial).as_posix(): sha(p) for p in sorted(trial.rglob("*")) if p.is_file()}
        (evidence / "staged-sha256.json").write_text(json.dumps(staged, indent=1) + "\n")
        try:
            worker = Worker(trial, runtime, runtime / "bin/python", evidence / "audit",
                            trusted_read_roots=[UV_PYTHON], timeout_seconds=REPLAY_TIMEOUT,
                            max_output_bytes=65536)
            result = worker.run_python(["analysis.py"], request={"tool": "replay"})
        except (BoundaryError, OSError, ValueError) as exc:
            return out | {"outcome": "infrastructure", "error": f"{type(exc).__name__}: {exc}"}
        out["execution"] = {k: result.get(k) for k in ("status", "exit_code", "code")} | {
            "stderr_tail": (result.get("stderr") or "")[-800:]}
        if result.get("code") == "execution_failed":
            return out | {"outcome": "infrastructure", "error": result.get("message")}
        regenerated, regenerated_digest, error = load_results(trial / "results.json")
        if result.get("status") != "ok" or regenerated is None:
            return out | {"outcome": "failed", "error": error}
        shutil.copyfile(trial / "results.json", evidence / "results.json")
    out["regenerated_results_sha256"] = regenerated_digest
    if not agree(original, regenerated, TOLERANCE):
        return out | {"outcome": "mismatch", "evidence_dir": str(evidence)}
    return out | {"outcome": "replayed", "byte_identical": digest == regenerated_digest,
                  "provenance_review_required": True, "evidence_dir": str(evidence)}


def run_session(session, plan, out_dir):
    record = Path(out_dir) / "sessions" / session["session_id"]
    record.mkdir(parents=True, exist_ok=False)
    work = Path(tempfile.mkdtemp(prefix="authentic-", dir=plan["work_root"]))
    trial_root = work / "trial"
    (record / "started.json").write_text(json.dumps({"session": session, "scratch": str(work),
                                                     "started_unix": time.time()}) + "\n")
    summary = {"session": session, "scratch": str(work), "complete": False}
    events, breach, proc = [], [], None
    try:
        if fingerprints(plan["runtime_root"], plan["cases_dir"]) != plan["fingerprints"]:
            raise Halt("frozen fingerprints differ")
        if {name: sha(launch.REPO / name) for name in SOURCE} != plan["session_source"]:
            raise Halt("session source differs from the plan")
        materials = verify_materials(plan["cases_dir"], session["case"])
        summary["organisation_policy"] = verify_config_dir(plan["config_dir"])
        inventory = capture_inventory(plan["runtime_root"], session["arm"], plan["model"],
                                      plan["capture_config_dir"], record / "inventory-capture.json")
        if inventory != plan["inventory"][session["arm"]]:
            raise Halt(f"captured inventory differs: {inventory}")
        mcp = stage(trial_root, materials, plan["runtime_root"], session["arm"], record / "worker-audit")
        home = supervisor_home(work / "home")
        no_instruction_ancestors(home)
        summary["auth"] = subscription_status(home, plan["config_dir"])
        text = session_prompt(session["case"], session["arm"])
        (record / "prompt.md").write_text(text)
        proc = subprocess.Popen(main_command(text, mcp, plan["max_turns"], plan["model"]), cwd=home,
                                env=environment(home, plan["config_dir"]), stdin=subprocess.DEVNULL,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, start_new_session=True, text=True)
        advertised = sorted(t for t in plan["inventory"][session["arm"]] if t != "DeferredToolPlaceholder")

        def check(event):
            if event.get("type") == "system" and event.get("subtype") == "init" and \
                    sorted(event.get("tools", [])) != advertised:
                breach.append("init_inventory")
                os.killpg(proc.pid, signal.SIGKILL)

        reader = stream(proc, events, check)
        summary["termination"] = "exited"
        try:
            proc.wait(timeout=plan["wall_seconds"])
        except subprocess.TimeoutExpired:
            summary["termination"] = "wall_limit"
        reader.join(timeout=5)
    finally:
        try:
            summary["terminated_groups"] = terminate(proc.pid if proc else None, record / "worker-audit")
        finally:
            (record / "transcript.jsonl").write_text("".join(json.dumps(e) + "\n" for e in events))
            if proc is not None:
                (record / "stderr.txt").write_text(proc.stderr.read() if proc.stderr else "")
            (record / "session.json").write_text(json.dumps(summary, indent=1) + "\n")
    if not any(e.get("type") == "system" and e.get("subtype") == "init" for e in events):
        breach.append("no_init_record")
    result = next((e for e in reversed(events) if e.get("type") == "result"), None)
    usage = (result or {}).get("usage")
    summary.update(exit_code=proc.returncode, breach=breach, result_subtype=(result or {}).get("subtype"),
                   usage=usage, num_turns=(result or {}).get("num_turns"),
                   duration_ms=(result or {}).get("duration_ms"))
    summary["refused_exports"] = export(trial_root, record / "workspace")
    summary["reconciliation"] = reconcile(events, record / "worker-audit", plan["inventory"][session["arm"]])
    if complete_usage(usage):
        summary["counted_tokens"] = sum(usage[k] for k in USAGE_FIELDS[:3])
        summary["cache_read_tokens"] = usage["cache_read_input_tokens"]

    session_id = next((e.get("session_id") for e in events if e.get("type") == "system"
                       and e.get("subtype") == "init"), None)
    if session_id and summary["termination"] == "exited":
        retro_mcp, retro_audit = retrospective_mcp(work)
        retro_events, retro = [], None
        try:
            retro = subprocess.Popen(retrospective_command(session_id, retro_mcp, plan["model"]), cwd=work / "home",
                                     env=environment(work / "home", plan["config_dir"]), stdin=subprocess.DEVNULL,
                                     stdout=subprocess.PIPE, stderr=subprocess.PIPE, start_new_session=True,
                                     text=True)
            reader = stream(retro, retro_events)
            try:
                retro.wait(timeout=300)
            except subprocess.TimeoutExpired:
                pass
            reader.join(timeout=5)
        finally:
            terminate(retro.pid if retro else None, retro_audit)
        (record / "retrospective.jsonl").write_text("".join(json.dumps(e) + "\n" for e in retro_events))
        retro_result = next((e for e in reversed(retro_events) if e.get("type") == "result"), None) or {}
        retro_tools = [b for e in retro_events if e.get("type") == "assistant"
                       for b in e.get("message", {}).get("content", []) if b.get("type") == "tool_use"]
        summary["retrospective"] = {"text": retro_result.get("result"), "subtype": retro_result.get("subtype"),
                                    "usage": retro_result.get("usage"), "attempted_tool_uses": len(retro_tools)}
        if complete_usage(retro_result.get("usage")):
            summary["retrospective"]["counted_tokens"] = sum(retro_result["usage"][k] for k in USAGE_FIELDS[:3])
        else:
            breach.append("retrospective_usage")
    try:
        summary["organisation_policy_after"] = verify_config_dir(plan["config_dir"])
    except Halt as exc:
        breach.append(f"configuration_after: {exc}")

    (record / "replay").mkdir()
    summary["replay"] = replay(record, plan["cases_dir"], session["case"],
                               Path(plan["runtime_root"]) / session["arm"])
    if summary["replay"]["outcome"] == "infrastructure":
        breach.append("replay_infrastructure")
    summary["complete"] = not breach and summary["reconciliation"]["consistent"] and complete_usage(usage)
    summary["finished_unix"] = time.time()
    (record / "session.json").write_text(json.dumps(summary, indent=1) + "\n")
    if summary["complete"]:
        shutil.rmtree(work)
    else:
        raise Halt(f"{session['session_id']}: breach {breach}, reconciliation "
                   f"{summary['reconciliation']['problems']}, usage complete {complete_usage(usage)}")
    return summary


def make_plan(path, *, runtime_root, work_root, config_dir, capture_config_dir, ceiling, sessions,
              max_turns=80, wall_seconds=1800, model=launch.MODEL):
    arms = sorted({s["arm"] for s in sessions})
    plan = {"model": model, "runtime_root": str(Path(runtime_root).resolve()), "cases_dir": str(CASES),
            "config_dir": str(Path(config_dir).resolve()),
            "capture_config_dir": str(Path(capture_config_dir).resolve()),
            "fingerprints": fingerprints(runtime_root, CASES),
            "session_source": {name: sha(launch.REPO / name) for name in SOURCE},
            "inventory": {arm: capture_inventory(runtime_root, arm, model, capture_config_dir) for arm in arms},
            "work_root": str(Path(work_root).resolve()), "max_turns": max_turns, "wall_seconds": wall_seconds,
            "counted_token_ceiling": ceiling, "sessions": sessions}
    with Path(path).open("x") as out:
        out.write(json.dumps(plan, indent=1) + "\n")
    return plan


def spent_so_far(out_dir):
    out_dir = Path(out_dir)
    if (out_dir / "HALTED.json").exists():
        raise Halt("run is halted; see HALTED.json")
    spent = 0
    for directory in sorted((out_dir / "sessions").glob("*")):
        summary = json.loads((directory / "session.json").read_text()) if (directory / "session.json").exists() else {}
        if not summary.get("complete"):
            raise Halt(f"earlier session did not complete cleanly: {directory.name}")
        spent += summary["counted_tokens"] + summary.get("retrospective", {}).get("counted_tokens", 0)
    return spent


def run(plan_path, out_dir, only=None):
    plan = json.loads(Path(plan_path).read_text())
    digest = sha(plan_path)
    out_dir = Path(out_dir)
    (out_dir / "sessions").mkdir(parents=True, exist_ok=True)
    binding = out_dir / "PLAN.sha256"
    log = []
    try:
        if binding.exists() and binding.read_text().strip() != digest:
            raise Halt("output directory belongs to a different plan")
        binding.write_text(digest + "\n")
        spent = spent_so_far(out_dir)
        for session in plan["sessions"]:
            if only and session["session_id"] not in only:
                continue
            if (out_dir / "sessions" / session["session_id"]).exists():
                continue
            if spent >= plan["counted_token_ceiling"]:
                log.append({"stop": "ceiling", "spent": spent})
                break
            summary = run_session(session, plan, out_dir)
            used = summary["counted_tokens"] + summary.get("retrospective", {}).get("counted_tokens", 0)
            spent += used
            log.append({"session": session["session_id"], "counted": used, "replay": summary["replay"]["outcome"]})
    except Halt as exc:
        log.append({"halt": str(exc)})
        if not (out_dir / "HALTED.json").exists():
            (out_dir / "HALTED.json").write_text(json.dumps({"halt": str(exc), "time_unix": time.time()}) + "\n")
    with (out_dir / "run_log.jsonl").open("a") as stream_out:
        for entry in log:
            stream_out.write(json.dumps(entry) + "\n")
    return log


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("plan")
    p.add_argument("plan")
    for name in ("--runtime", "--work-root", "--config-dir", "--capture-config-dir"):
        p.add_argument(name, required=True)
    p.add_argument("--ceiling", type=int, required=True)
    p.add_argument("--session", action="append", required=True, help="ID:CASE:ARM")
    r = sub.add_parser("run")
    r.add_argument("plan")
    r.add_argument("out_dir")
    r.add_argument("--only", nargs="*")
    args = parser.parse_args()
    if args.cmd == "plan":
        sessions = [dict(zip(("session_id", "case", "arm"), s.split(":"))) for s in args.session]
        make_plan(args.plan, runtime_root=args.runtime, work_root=args.work_root, config_dir=args.config_dir,
                  capture_config_dir=args.capture_config_dir, ceiling=args.ceiling, sessions=sessions)
        print(args.plan)
    else:
        print(json.dumps(run(args.plan, args.out_dir, args.only), indent=1))


if __name__ == "__main__":
    main()
