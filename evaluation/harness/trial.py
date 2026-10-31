"""Run one agent trial in a fresh, externally sandboxed workspace and preserve its record."""

import argparse
import hashlib
import json
import os
import secrets
import shutil
import signal
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

from sandbox import profile

REPO = Path(__file__).resolve().parents[2]
EVAL = REPO / "evaluation"
ROOT = Path.home() / "palaeo-eval"
RUNTIME = ROOT / "runtime"
PROMPT = (EVAL / "harness/prompt.md").read_text()
TOOLKIT_NOTE = (EVAL / "harness/prompt-toolkit.md").read_text()
SCHEMA = EVAL / "answer.schema.json"
BACKENDS = {
    "codex": {"model": "gpt-6.1-sol", "effort": "medium"},
    "claude": {"model": "claude-sonnet-5-5", "effort": None},
}


def sha256_bytes(data):
    return hashlib.sha256(data).hexdigest()


def prepare(materials, arm, trial_root):
    ws = trial_root / "ws"
    shutil.copytree(materials, ws)
    shutil.copy(SCHEMA, ws / "answer.schema.json")
    if arm == "toolkit":
        shutil.copy(RUNTIME / "palaeo_agent_discover.json", ws / "palaeo_agent_discover.json")
    for name in ("home", "tmp"):
        (trial_root / name).mkdir()
    return ws


def command(backend, arm, ws, prompt, trial_root):
    cfg = BACKENDS[backend]
    venv_bin = RUNTIME / arm / "bin"
    env = {"PATH": f"{venv_bin}:/usr/bin:/bin", "TMPDIR": str(trial_root / "tmp"), "LANG": "en_AU.UTF-8",
           "USER": os.environ["USER"], "LOGNAME": os.environ["USER"], "VIRTUAL_ENV": str(RUNTIME / arm)}
    if backend == "codex":
        home = trial_root / "home"
        shutil.copy(Path.home() / ".codex/auth.json", home / "auth.json")
        env.update(HOME=str(home), CODEX_HOME=str(home))
        argv = ["/opt/homebrew/bin/codex", "exec", "--ephemeral", "--ignore-user-config", "--ignore-rules",
                "--skip-git-repo-check", "--json", "--cd", str(ws), "-m", cfg["model"],
                "-c", f"model_reasoning_effort=\"{cfg['effort']}\"", "-c", "approval_policy=\"never\"", "-c", "web_search=\"disabled\"",
                "--dangerously-bypass-approvals-and-sandbox", "-o", str(trial_root / "last_message.txt"), prompt]
    else:
        env["HOME"] = str(Path.home())
        argv = ["/opt/homebrew/bin/claude", "-p", prompt, "--model", cfg["model"], "--strict-mcp-config",
                "--setting-sources", "", "--no-session-persistence", "--output-format", "stream-json",
                "--verbose", "--exclude-dynamic-system-prompt-sections", "--permission-mode", "bypassPermissions",
                "--tools", "Bash,Read,Edit,Write"]
    return argv, env


def account_email():
    try:
        return json.loads((Path.home() / ".claude.json").read_text())["oauthAccount"]["emailAddress"]
    except (OSError, KeyError, json.JSONDecodeError):
        return None


def redact(directory):
    email = account_email()
    if not email:
        return
    for path in Path(directory).rglob("*"):
        if path.is_file():
            try:
                text = path.read_text()
            except UnicodeDecodeError:
                continue
            if email in text:
                path.write_text(text.replace(email, "<account-email>"))


def usage(backend, transcript):
    totals = {}
    for line in transcript.splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if backend == "codex" and event.get("type") == "turn.completed":
            for key, value in event.get("usage", {}).items():
                if isinstance(value, (int, float)):
                    totals[key] = totals.get(key, 0) + value
        if backend == "claude" and event.get("type") == "result":
            for key, value in (event.get("usage") or {}).items():
                if isinstance(value, (int, float)):
                    totals[key] = value
            totals["total_cost_usd"] = event.get("total_cost_usd")
            totals["num_turns"] = event.get("num_turns")
    return totals


COUNTED = {
    "codex": "input_tokens - cached_input_tokens + output_tokens, summed over turn.completed events",
    "claude": "input_tokens + cache_creation_input_tokens + output_tokens from the result event; cache reads reported separately",
}


def counted_tokens(backend, totals):
    if backend == "codex":
        return (totals.get("input_tokens", 0) - totals.get("cached_input_tokens", 0)) + totals.get("output_tokens", 0)
    return totals.get("input_tokens", 0) + totals.get("cache_creation_input_tokens", 0) + totals.get("output_tokens", 0)


def run(materials, arm, backend, record_dir, wall_seconds=300, prompt_override=None):
    trial_id = secrets.token_hex(6)
    trial_root = ROOT / "t" / trial_id
    trial_root.mkdir(parents=True)
    ws = prepare(materials, arm, trial_root)
    prompt = prompt_override or (PROMPT + (TOOLKIT_NOTE if arm == "toolkit" else ""))
    argv, env = command(backend, arm, ws, prompt, trial_root)
    sb = profile(backend=backend, trial_root=trial_root, runtime=RUNTIME / arm)
    (trial_root / "sandbox.sb").write_text(sb)
    started = datetime.now(timezone.utc)
    t0 = time.monotonic()
    proc = subprocess.Popen(["/usr/bin/sandbox-exec", "-f", str(trial_root / "sandbox.sb"), *argv], cwd=ws, env=env,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.DEVNULL,
                            start_new_session=True)
    termination = "exited"
    try:
        out, err = proc.communicate(timeout=wall_seconds)
    except subprocess.TimeoutExpired:
        os.killpg(proc.pid, signal.SIGTERM)
        try:
            out, err = proc.communicate(timeout=10)
        except subprocess.TimeoutExpired:
            os.killpg(proc.pid, signal.SIGKILL)
            out, err = proc.communicate()
        termination = "wall_limit"
    elapsed = time.monotonic() - t0
    record_dir = Path(record_dir)
    record_dir.mkdir(parents=True, exist_ok=False)
    transcript = out.decode(errors="replace")
    (record_dir / "transcript.jsonl").write_text(transcript)
    (record_dir / "stderr.txt").write_text(err.decode(errors="replace"))
    (record_dir / "sandbox.sb").write_text(sb.replace(trial_id, "<trial>"))
    shutil.copytree(ws, record_dir / "workspace")
    if (trial_root / "last_message.txt").exists():
        shutil.copy(trial_root / "last_message.txt", record_dir / "last_message.txt")
    redact(record_dir)
    totals = usage(backend, transcript)
    version = subprocess.run([argv[0], "--version"], capture_output=True, text=True).stdout.strip()
    meta = {"trial_id": trial_id, "materials": str(Path(materials).relative_to(REPO)) if Path(materials).is_relative_to(REPO) else str(materials),
            "arm": arm, "backend": backend, **BACKENDS[backend], "cli_version": version,
            "argv": [a if a != prompt else "<prompt>" for a in argv],
            "env_keys": sorted(env), "prompt_sha256": sha256_bytes(prompt.encode()),
            "runtime": json.loads((RUNTIME / "runtime.json").read_text()) | {"arms": None},
            "started_utc": started.isoformat(), "elapsed_seconds": round(elapsed, 1), "wall_limit_seconds": wall_seconds,
            "termination": termination, "returncode": proc.returncode, "usage": totals,
            "counted_tokens": counted_tokens(backend, totals)}
    (record_dir / "trial.json").write_text(json.dumps(meta, indent=1) + "\n")
    shutil.rmtree(trial_root)
    return meta


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("materials", type=Path)
    parser.add_argument("arm", choices=["direct", "toolkit"])
    parser.add_argument("backend", choices=list(BACKENDS))
    parser.add_argument("record_dir", type=Path)
    parser.add_argument("--wall-seconds", type=int, default=300)
    parser.add_argument("--prompt-file", type=Path)
    args = parser.parse_args()
    meta = run(args.materials, args.arm, args.backend, args.record_dir, args.wall_seconds,
               args.prompt_file.read_text() if args.prompt_file else None)
    print(json.dumps({k: meta[k] for k in ("trial_id", "termination", "elapsed_seconds", "usage", "counted_tokens")}))
