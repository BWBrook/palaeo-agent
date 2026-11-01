"""Pilot launcher, Claude route, subscription authentication (docs/pilot-protocol.md, launch conditions).

The supervisor is Claude Code in its normal mode, authenticated by Barry's
subscription through a dedicated configuration directory that holds no
instructions, memory, skills or plugins. Every trial:

- verifies the frozen fingerprints (client, the full bytes of both runtimes and
  their base interpreter, worker and launcher source, prompts, item materials)
  and the configuration directory's contents;
- stages exactly the item's manifest-listed materials;
- checks the subscription login in the supervisor's own launch environment (a
  fresh HOME whose only content is a link to the login keychain);
- captures the identical command's request against a fake local endpoint and
  requires the frozen tool inventory (the capture is saved);
- requires the client's init record to match that inventory;
- reconciles every tool event with the worker audit by its full arguments and
  the exact value the adapter returned, one use to one result to one record;
- kills the client group, then the worker server and every recorded worker
  process group, and verifies they are gone;
- exports only regular files, never following links;
- requires complete usage accounting;
- replays the package end to end from pristine materials (replay.py); a replay
  infrastructure failure halts for diagnosis.

Any failure writes HALTED.json; no later launch runs until it is resolved.
A started trial is never rerun.

    python evaluation/pilot/launch.py plan ITEMS_DIR PLAN.json --runtime R --work-root W --config-dir C --ceiling N
    python evaluation/pilot/launch.py run PLAN.json OUT_DIR
"""

import argparse
import hashlib
import json
import os
import pwd
from pathlib import Path
import random
import shutil
import signal
import stat
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
PINNED_SOURCE = ["evaluation/execution/__init__.py", "evaluation/execution/server.py",
                 "evaluation/execution/worker.py", "evaluation/pilot/launch.py", "evaluation/pilot/score.py",
                 "evaluation/revised/score.py", "evaluation/sprint3/claude-client-boundary/probe.py",
                 "evaluation/pilot/replay.py"]
CONFIG_ALLOWED = {".claude.json", ".claude.json.backup", "statsig", "todos", "shell-snapshots", "projects",
                  ".credentials.json", "backups", "session-env", "cache", "sessions", ".last-cleanup",
                  "remote-settings.json", "policy-limits.json"}
MANAGED_SIDECARS = ("remote-settings.json.", "policy-limits.json.")
POLICY_KEYS = {"restrictions", "compliance_taints", "monitoring_notice", "defaults"}
CONFIG_FORBIDDEN = {"CLAUDE.md", "agents", "commands", "skills", "plugins", "hooks", "settings.json",
                    "settings.local.json", "output-styles", "rules"}
USAGE_FIELDS = ("input_tokens", "cache_creation_input_tokens", "output_tokens", "cache_read_input_tokens")


class Halt(RuntimeError):
    pass


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def client_path():
    return Path(shutil.which("claude")).resolve()


def prompt(arm):
    text = (PROMPTS / "analyst.md").read_text()
    return text + (PROMPTS / "analyst-toolkit.md").read_text() if arm == "toolkit" else text


def tree_digest(root):
    """One digest over every entry under root: file bytes, link targets and directories, never following links."""
    root, digest = Path(root), hashlib.sha256()
    for parent, folders, files in os.walk(root, followlinks=False):
        folders.sort()
        for name in sorted(folders + files):
            path = Path(parent) / name
            info = path.lstat()
            if stat.S_ISLNK(info.st_mode):
                entry = f"l {os.readlink(path)}"
            elif stat.S_ISREG(info.st_mode):
                entry = f"f {sha(path)}"
            elif stat.S_ISDIR(info.st_mode):
                entry = "d"
            else:
                entry = f"s {stat.S_IFMT(info.st_mode)}"
            digest.update(f"{path.relative_to(root).as_posix()}\0{entry}\n".encode())
    return digest.hexdigest()


def fingerprints(runtime_root, items_dir):
    runtime_root = Path(runtime_root)
    site = lambda arm: next((runtime_root / arm / "lib").glob("python3.*/site-packages"))
    return {"client_sha256": sha(client_path()),
            "runtime_tree": tree_digest(runtime_root),
            "base_interpreter_tree": tree_digest(UV_PYTHON),
            "direct_has_toolkit": (site("direct") / "palaeo_agent").exists(),
            "source": {name: sha(REPO / name) for name in PINNED_SOURCE},
            "prompts": {p.name: sha(p) for p in sorted(PROMPTS.glob("*.md"))},
            "items_manifest_sha256": sha(Path(items_dir) / "MANIFEST.json")}


def verify_materials(items_dir, item):
    """The item's files must equal the manifest exactly; return the materials to stage."""
    items_dir = Path(items_dir)
    manifest = {k: v for k, v in json.loads((items_dir / "MANIFEST.json").read_text()).items()
                if k.startswith(f"{item}/")}
    present = {}
    for parent, folders, files in os.walk(items_dir / item, followlinks=False):
        for name in folders + files:
            path = Path(parent) / name
            if path.is_symlink() or not (path.is_dir() or stat.S_ISREG(path.lstat().st_mode)):
                raise Halt(f"item holds a link or special file: {path}")
            if path.is_file():
                present[path.relative_to(items_dir).as_posix()] = path
    if set(present) != set(manifest):
        raise Halt(f"item files differ from manifest: extra {sorted(set(present) - set(manifest))}, "
                   f"missing {sorted(set(manifest) - set(present))}")
    for name, digest in manifest.items():
        if sha(present[name]) != digest:
            raise Halt(f"item file differs from manifest: {name}")
    materials = [present[n] for n in sorted(present) if n.startswith(f"{item}/materials/")]
    if any(p.parent != items_dir / item / "materials" for p in materials):
        raise Halt("item materials must be a flat directory")
    return materials


def verify_config_dir(config_dir):
    config_dir = Path(config_dir)
    names = {p.name for p in config_dir.iterdir() if not (p.name.startswith(MANAGED_SIDECARS) and p.is_file())}
    if names & CONFIG_FORBIDDEN or names - CONFIG_ALLOWED:
        raise Halt(f"configuration directory holds unexpected entries: {sorted(names - CONFIG_ALLOWED)}")
    projects = config_dir / "projects"
    if projects.exists() and any(p.is_file() and ("memory" in p.relative_to(projects).parts or p.suffix == ".md")
                                 for p in projects.rglob("*")):
        raise Halt("configuration directory holds project memory")
    # A subscription login fetches the organisation's signed managed files. Managed settings could change the
    # client's behaviour, so they must be empty; product policy limits are recorded.
    remote = config_dir / "remote-settings.json"
    if remote.exists() and json.loads(remote.read_text()) != {}:
        raise Halt("organisation-managed settings are present")
    policy = config_dir / "policy-limits.json"
    if not policy.exists():
        return {}
    limits = json.loads(policy.read_text())
    if set(limits) - POLICY_KEYS:
        raise Halt(f"unrecognised policy-limit fields: {sorted(set(limits) - POLICY_KEYS)}")
    return {"policy_limits_sha256": sha(policy), "policy_limits": limits}


def supervisor_home(home, keychain=True):
    """A fresh HOME for the client. Its only content is a link to the user's login keychain, which macOS
    locates through HOME and which holds the subscription login; the capture home omits even that."""
    home = Path(home)
    (home / "Library").mkdir(parents=True)
    if keychain:
        (home / "Library/Keychains").symlink_to(Path(pwd.getpwuid(os.getuid()).pw_dir) / "Library/Keychains")
    return home


def subscription_status(home, config_dir):
    """Login state in the exact environment the client will be launched with."""
    completed = subprocess.run([str(client_path()), "auth", "status", "--json"], capture_output=True, text=True,
                               cwd=home, env=environment(home, config_dir), timeout=60)
    status = json.loads(completed.stdout or "{}")
    kept = {k: status.get(k) for k in ("loggedIn", "authMethod", "subscriptionType", "apiProvider")}
    if not kept["loggedIn"] or "api" in str(kept.get("authMethod", "")).lower():
        raise Halt(f"configuration directory is not logged in to a subscription: {kept}")
    return kept


def no_instruction_ancestors(path):
    for parent in [Path(path), *Path(path).parents]:
        for name in ("CLAUDE.md", "CLAUDE.local.md", ".claude"):
            if (parent / name).exists():
                raise Halt(f"instruction file above the client's working directory: {parent / name}")


def stage(trial_root, materials, runtime_root, arm, audit_dir):
    trial_root.mkdir(parents=True)
    for source in materials:
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


def command(text, mcp, max_turns, model):
    return [str(client_path()), "-p", text, "--tools=", "--strict-mcp-config", "--mcp-config", str(mcp),
            "--setting-sources=", "--no-session-persistence", "--permission-mode", "bypassPermissions",
            "--allowedTools", "mcp__worker__*", "--model", model, "--max-turns", str(max_turns),
            "--output-format", "stream-json", "--verbose"]


def environment(home, config_dir, api_key=None, base_url=None):
    env = {"PATH": "/usr/bin:/bin:/opt/homebrew/bin", "HOME": str(home), "USER": os.environ["USER"],
           "LOGNAME": os.environ["USER"], "CLAUDE_CONFIG_DIR": str(config_dir), "DISABLE_TELEMETRY": "1",
           "DISABLE_ERROR_REPORTING": "1", "CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC": "1",
           "MAX_MCP_OUTPUT_TOKENS": "200000", "CLAUDE_CODE_DISABLE_AUTO_MEMORY": "1"}
    if api_key:
        env["ANTHROPIC_API_KEY"] = api_key
    if base_url:
        env["ANTHROPIC_BASE_URL"] = base_url
    return env


def living_groups(groups):
    """Groups that still hold a non-zombie process; a failed enumeration is an error, never empty."""
    listing = subprocess.run(["/bin/ps", "-A", "-o", "pgid=,stat="], capture_output=True, text=True)
    if listing.returncode != 0 or not listing.stdout.strip():
        raise Halt("process enumeration failed")
    alive = set()
    for line in listing.stdout.splitlines():
        pgid, state = line.split()
        if int(pgid) in groups and not state.startswith("Z"):
            alive.add(int(pgid))
    return alive


def terminate(client_pgid, audit_dir):
    """Kill the client group, the worker server and every recorded worker group; verify all are gone."""
    groups = set()
    if client_pgid:
        groups.add(client_pgid)
    audit_dir = Path(audit_dir)
    if (audit_dir / "server.pid").exists():
        pid, pgid = map(int, (audit_dir / "server.pid").read_text().split())
        groups.add(pgid)
        try:
            os.kill(pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
    if (audit_dir / "pids.jsonl").exists():
        groups |= {json.loads(line)["pgid"] for line in (audit_dir / "pids.jsonl").read_text().splitlines()}
    groups.discard(os.getpgid(0))
    for group in groups:
        try:
            os.killpg(group, signal.SIGKILL)
        except ProcessLookupError:
            pass
    deadline = time.monotonic() + 5
    alive = living_groups(groups)
    while alive and time.monotonic() < deadline:
        time.sleep(0.05)
        alive = living_groups(groups)
    if alive:
        raise Halt(f"process groups survived termination: {sorted(alive)}")
    return sorted(groups)


def capture_inventory(runtime_root, arm, model, config_dir, record=None):
    """Offline: the request the identical command builds, from a fake endpoint with a dummy key."""
    with tempfile.TemporaryDirectory() as scratch:
        scratch = Path(scratch)
        (scratch / "task.md").write_text("inventory capture\n")
        audit = scratch / "audit"
        mcp = stage(scratch / "work/trial", [scratch / "task.md"], runtime_root, arm, audit)
        supervisor_home(scratch / "home", keychain=False)
        log = []
        server = endpoint([], log)
        proc = subprocess.Popen(command(prompt(arm), mcp, 2, model), cwd=scratch / "home",
                                env=environment(scratch / "home", config_dir, DUMMY,
                                                f"http://127.0.0.1:{server.server_address[1]}"),
                                stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                start_new_session=True)
        try:
            proc.communicate(timeout=120)
        except subprocess.TimeoutExpired:
            pass
        finally:
            server.shutdown()
            terminate(proc.pid, audit)
        if not log:
            raise Halt("inventory capture produced no request")
        if any(r["authorization_header"] or not r["dummy_api_key"] for r in log):
            raise Halt("inventory capture would have sent a real credential")
        if record is not None:
            Path(record).write_text(json.dumps({"requests": log, "arm": arm}, indent=1) + "\n")
        return sorted(log[0]["tools"])


def export(trial_root, destination):
    """Copy regular files only, never following links; return what was refused."""
    refused = []
    for parent, folders, files in os.walk(trial_root, followlinks=False):
        relative = Path(parent).relative_to(trial_root)
        if relative.parts[:1] == (".worker",):
            continue
        for name in folders:
            if (Path(parent) / name).is_symlink():
                refused.append({"path": (relative / name).as_posix(), "kind": "link",
                                "target": os.readlink(Path(parent) / name)})
        for name in files:
            source = Path(parent) / name
            info = source.lstat()
            if not stat.S_ISREG(info.st_mode):
                refused.append({"path": (relative / name).as_posix(),
                                "kind": "link" if stat.S_ISLNK(info.st_mode) else "special",
                                **({"target": os.readlink(source)} if stat.S_ISLNK(info.st_mode) else {})})
                continue
            target = destination / relative / name
            target.parent.mkdir(parents=True, exist_ok=True)
            descriptor = os.open(source, os.O_RDONLY | os.O_NOFOLLOW)
            with os.fdopen(descriptor, "rb") as stream:
                target.write_bytes(stream.read())
    return refused


def worker_requests(name, arguments, result):
    """The audit requests the fixed adapter can record for this call (server.ExecutionTransport, Worker)."""
    tool = name.removeprefix("mcp__worker__")
    if tool == "worker_execute":
        forms = [{"tool": tool, "code": arguments.get("code")}]
    elif tool == "worker_read":
        forms = [{"tool": tool, "path": arguments.get("path"), "offset": arguments.get("offset", 0),
                  "limit": arguments.get("limit", 32768)}]
    elif tool == "worker_write":
        forms = [{"tool": tool, "path": arguments.get("path"), "content": arguments.get("content")}]
    else:
        forms = [{"tool": tool.removeprefix("palaeo_"), "arguments": arguments}]
    if result.get("code") == "invalid_arguments":
        forms += [{"tool": tool, "arguments": arguments}, {"tool": tool},
                  {"tool": tool, "path": arguments.get("path")}]
    return forms


def adapter_value(name, result):
    """The value the adapter returns to the client for an audited worker result (server.ExecutionTransport)."""
    if name.startswith("mcp__worker__worker_") or result.get("code") == "invalid_arguments":
        return result
    if result.get("truncated", {}).get("stdout"):
        return {"status": "error", "code": "output_limit", "execution": result}
    try:
        value = json.loads(result["stdout"])
    except (ValueError, KeyError, TypeError):
        return {"status": "error", "code": "worker_failed", "execution": result}
    if result["status"] not in ("ok", "error") or result.get("exit_code") not in (0, 2):
        return {"status": "error", "code": "worker_failed", "execution": result}
    return value


def result_value(result):
    content = result.get("content")
    if isinstance(content, list):
        content = "".join(b.get("text", "") for b in content if isinstance(b, dict) and b.get("type") == "text")
    try:
        return json.loads(content)
    except (TypeError, ValueError):
        return None


def reconcile(events, audit_dir, inventory):
    """Pair every tool use with exactly one result and either one worker audit record (same full request,
    same returned value and error flag) or a client refusal; anything unpaired is a problem."""
    uses, results, problems = [], {}, []
    for event in events:
        message = event.get("message")
        for block in message.get("content", []) if isinstance(message, dict) and isinstance(message.get("content"), list) else []:
            if isinstance(block, dict) and block.get("type") == "tool_use":
                uses.append(block)
            elif isinstance(block, dict) and block.get("type") == "tool_result":
                if block.get("tool_use_id") in results:
                    problems.append({"id": block.get("tool_use_id"), "problem": "duplicate result"})
                results[block.get("tool_use_id")] = block
    ids = [u.get("id") for u in uses]
    problems += [{"id": i, "problem": "duplicate tool use id"} for i in sorted({i for i in ids if ids.count(i) > 1})]
    problems += [{"id": i, "problem": "result without tool use"} for i in results if i not in ids]
    path = Path(audit_dir) / "calls.jsonl"
    calls = [json.loads(line) for line in path.read_text().splitlines()] if path.exists() else []
    audit = [c for c in calls if c["request"].get("tool") != "supervisor_load_tool_definitions"]
    bootstrap = len(calls) - len(audit)
    matched, refused = 0, 0
    unmatched = list(range(len(audit)))
    for use in uses:
        result = results.get(use.get("id"))
        if result is None:
            problems.append({"id": use.get("id"), "problem": "no result"})
            continue
        text = json.dumps(result.get("content"))
        if use["name"] not in inventory:
            if result.get("is_error") and "No such tool available" in text:
                refused += 1
            else:
                problems.append({"id": use["id"], "problem": "unadvertised tool not refused", "name": use["name"]})
            continue
        if not use["name"].startswith("mcp__worker__"):
            problems.append({"id": use["id"], "problem": "advertised non-worker tool", "name": use["name"]})
            continue
        arguments = use.get("input") if isinstance(use.get("input"), dict) else {}
        candidates = [i for i in unmatched if audit[i]["request"] in worker_requests(use["name"], arguments,
                                                                                     audit[i]["result"])]
        if not candidates:
            problems.append({"id": use["id"], "problem": "no audit record with this request", "name": use["name"]})
            continue
        observed = result_value(result)
        for i in candidates:
            value = adapter_value(use["name"], audit[i]["result"])
            flagged = isinstance(value, dict) and value.get("status") in ("error", "timed_out", "different")
            if observed == value and bool(result.get("is_error")) == flagged:
                unmatched.remove(i)
                matched += 1
                break
        else:
            problems.append({"id": use["id"], "problem": "returned value differs from audit", "name": use["name"]})
    problems += [{"problem": "audit record without tool event", "tool": audit[i]["request"].get("tool")}
                 for i in unmatched]
    return {"worker": matched, "client_refusal": refused, "bootstrap": bootstrap, "problems": problems,
            "consistent": not problems}


def complete_usage(usage):
    return isinstance(usage, dict) and all(isinstance(usage.get(k), int) and usage[k] >= 0 for k in USAGE_FIELDS)


def run_trial(trial, plan, out_dir, api_key=None, base_url=None):
    record = Path(out_dir) / "trials" / trial["trial_id"]
    record.mkdir(parents=True, exist_ok=False)
    work = Path(tempfile.mkdtemp(prefix="pilot-", dir=plan["work_root"]))
    trial_root = work / "trial"
    (record / "started.json").write_text(json.dumps({"trial": trial, "scratch": str(work),
                                                     "started_unix": time.time()}) + "\n")
    summary = {"trial": trial, "scratch": str(work), "complete": False}
    events, breach, proc = [], [], None
    try:
        if fingerprints(plan["runtime_root"], plan["items_dir"]) != plan["fingerprints"]:
            raise Halt("frozen fingerprints differ")
        materials = verify_materials(plan["items_dir"], trial["item"])
        summary["organisation_policy"] = verify_config_dir(plan["config_dir"])
        inventory = capture_inventory(plan["runtime_root"], trial["arm"], plan["model"],
                                      plan["capture_config_dir"], record / "inventory-capture.json")
        if inventory != plan["inventory"][trial["arm"]]:
            raise Halt(f"captured inventory differs: {inventory}")
        audit = record / "worker-audit"
        mcp = stage(trial_root, materials, plan["runtime_root"], trial["arm"], audit)
        supervisor_home(work / "home", keychain=not base_url)
        no_instruction_ancestors(work / "home")
        if not base_url:
            summary["auth"] = subscription_status(work / "home", plan["config_dir"])
        proc = subprocess.Popen(command(prompt(trial["arm"]), mcp, plan["max_turns"], plan["model"]),
                                cwd=work / "home", env=environment(work / "home", plan["config_dir"], api_key, base_url),
                                stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                start_new_session=True, text=True)
        advertised = sorted(t for t in plan["inventory"][trial["arm"]] if t != "DeferredToolPlaceholder")

        def read():
            for line in proc.stdout:
                try:
                    event = json.loads(line)
                except ValueError:
                    continue
                events.append(event)
                if event.get("type") == "system" and event.get("subtype") == "init" and \
                        sorted(event.get("tools", [])) != advertised:
                    breach.append("init_inventory")
                    os.killpg(proc.pid, signal.SIGKILL)

        reader = threading.Thread(target=read, daemon=True)
        reader.start()
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
            (record / "trial.json").write_text(json.dumps(summary, indent=1) + "\n")
    try:
        summary["organisation_policy_after"] = verify_config_dir(plan["config_dir"])
    except Halt as exc:
        breach.append(f"configuration_after: {exc}")
    if not any(e.get("type") == "system" and e.get("subtype") == "init" for e in events):
        breach.append("no_init_record")
    result = next((e for e in reversed(events) if e.get("type") == "result"), None)
    usage = (result or {}).get("usage")
    summary.update(exit_code=proc.returncode, breach=breach, result_subtype=(result or {}).get("subtype"), usage=usage)
    summary["refused_exports"] = export(trial_root, record / "workspace")
    summary["reconciliation"] = reconcile(events, record / "worker-audit", plan["inventory"][trial["arm"]])
    if complete_usage(usage):
        summary["counted_tokens"] = sum(usage[k] for k in USAGE_FIELDS[:3])
        summary["cache_read_tokens"] = usage["cache_read_input_tokens"]
    summary["score"] = score(record / "workspace", Path(plan["items_dir"]) / trial["item"],
                             "wall_limit" if summary["termination"] == "wall_limit" else "exited")
    try:
        from evaluation.pilot.replay import replay
        summary["replay"] = replay(record, plan["items_dir"], plan["runtime_root"])
    except Exception as exc:
        summary["replay"] = {"outcome": "infrastructure", "error": f"{type(exc).__name__}: {exc}"}
    if summary["replay"]["outcome"] == "infrastructure":
        breach.append("replay_infrastructure")
    summary["complete"] = not breach and summary["reconciliation"]["consistent"] and complete_usage(usage)
    summary["finished_unix"] = time.time()
    (record / "trial.json").write_text(json.dumps(summary, indent=1) + "\n")
    if summary["complete"]:
        shutil.rmtree(work)
    else:
        raise Halt(f"{trial['trial_id']}: breach {breach}, reconciliation {summary['reconciliation']['problems']}, "
                   f"usage complete {complete_usage(usage)}")
    return summary


def make_plan(items_dir, path, *, runtime_root, work_root, config_dir, capture_config_dir, ceiling, sessions=2,
              seed=20261101, max_turns=60, wall_seconds=600, model=MODEL, families=None):
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
    plan = {"model": model, "runtime_root": str(Path(runtime_root).resolve()), "items_dir": str(items_dir),
            "config_dir": str(Path(config_dir).resolve()), "capture_config_dir": str(Path(capture_config_dir).resolve()),
            "fingerprints": fingerprints(runtime_root, items_dir),
            "inventory": {arm: capture_inventory(runtime_root, arm, model, capture_config_dir)
                          for arm in ("direct", "toolkit")},
            "work_root": str(Path(work_root).resolve()), "max_turns": max_turns, "wall_seconds": wall_seconds,
            "counted_token_ceiling": ceiling, "seed": seed, "trials": trials}
    with Path(path).open("x") as stream:
        stream.write(json.dumps(plan, indent=1) + "\n")
    return plan


def ledger(out_dir, plan_digest):
    """Refuse to continue unless every earlier trial completed cleanly under this plan."""
    out_dir = Path(out_dir)
    if (out_dir / "HALTED.json").exists():
        raise Halt("run is halted; see HALTED.json")
    binding = out_dir / "PLAN.sha256"
    if binding.exists() and binding.read_text().strip() != plan_digest:
        raise Halt("output directory belongs to a different plan")
    spent = 0
    for directory in sorted((out_dir / "trials").glob("*")):
        path = directory / "trial.json"
        summary = json.loads(path.read_text()) if path.exists() else {}
        if not summary.get("complete"):
            raise Halt(f"earlier trial did not complete cleanly: {directory.name}")
        spent += summary["counted_tokens"]
    return spent


def run(plan_path, out_dir, api_key=None, base_url=None):
    plan = json.loads(Path(plan_path).read_text())
    digest = sha(plan_path)
    out_dir = Path(out_dir)
    (out_dir / "trials").mkdir(parents=True, exist_ok=True)
    log = []
    try:
        spent = ledger(out_dir, digest)
        if not (out_dir / "PLAN.sha256").exists():
            (out_dir / "PLAN.sha256").write_text(digest + "\n")
        for trial in plan["trials"]:
            if (out_dir / "trials" / trial["trial_id"]).exists():
                continue
            if spent >= plan["counted_token_ceiling"]:
                log.append({"stop": "ceiling", "spent": spent})
                break
            summary = run_trial(trial, plan, out_dir, api_key, base_url)
            spent += summary["counted_tokens"]
            log.append({"trial": trial["trial_id"], "outcome": summary["score"]["outcome"],
                        "counted": summary["counted_tokens"]})
    except Halt as exc:
        log.append({"halt": str(exc)})
        if not (out_dir / "HALTED.json").exists():
            (out_dir / "HALTED.json").write_text(json.dumps({"halt": str(exc), "time_unix": time.time()}) + "\n")
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
    for name in ("--runtime", "--work-root", "--config-dir", "--capture-config-dir"):
        p.add_argument(name, required=True)
    p.add_argument("--ceiling", type=int, required=True)
    p.add_argument("--sessions", type=int, default=2)
    p.add_argument("--families", nargs="*")
    r = commands.add_parser("run")
    r.add_argument("plan")
    r.add_argument("out_dir")
    args = parser.parse_args()
    if args.command == "plan":
        plan = make_plan(args.items_dir, args.plan, runtime_root=args.runtime, work_root=args.work_root,
                         config_dir=args.config_dir, capture_config_dir=args.capture_config_dir,
                         ceiling=args.ceiling, sessions=args.sessions, families=args.families)
        print(json.dumps({"trials": len(plan["trials"]), "inventory": plan["inventory"]}))
    else:
        print(json.dumps(run(args.plan, args.out_dir)))


if __name__ == "__main__":
    main()
