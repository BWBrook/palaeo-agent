"""Qualify the subscription supervisor environment: login state and instruction isolation, with no inference.

The launcher's exact command and environment are pointed at a local fake
endpoint that records every request body and answers with one line of text.
Each body is scanned for instruction markers: a planted canary, distinctive lines from the user's real global CLAUDE.md, policy
and memory, the client's own "Contents of" instruction preamble, and its
auto-memory section.

- capture: a fresh empty configuration and the capture home (no keychain link).
  No marker may appear.
- positive control: a canary CLAUDE.md inside a fresh configuration directory,
  with the user setting source switched on (the launcher passes an empty
  --setting-sources, which loads no CLAUDE.md at all). The canary and the
  preamble must appear, showing the scan detects instructions when they load.
- supervisor: the dedicated, logged-in configuration and the supervisor home
  (keychain link), with a dummy key and the fake endpoint. Login status is read
  in that same home first. No marker may appear. Which credential header the
  client sent is recorded as a boolean only; nothing leaves this machine.

Only booleans, counts and digests are saved; no body, credential or identity.

    python evaluation/pilot/qualify_supervisor.py RUNTIME_ROOT CONFIG_DIR RECEIPT.json
"""

import hashlib
import http.server
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import threading

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
from evaluation.pilot import launch  # noqa: E402

CANARY_CONFIG = "CANARY-CONFIG-CLAUDEMD-4402"
USER_CLAUDE = Path.home() / ".claude"


def user_markers():
    """Distinctive lines from the user's real instruction and memory files, if present."""
    markers = []
    for path in [USER_CLAUDE / "CLAUDE.md", USER_CLAUDE / "policy/shared.md", *USER_CLAUDE.glob("projects/*/memory/*.md")]:
        lines = [l.strip() for l in path.read_text().splitlines() if len(l.strip()) > 30] if path.is_file() else []
        markers += lines[:2]
    return markers


def fake(log):
    class Handler(http.server.BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def do_POST(self):
            body = self.rfile.read(int(self.headers.get("content-length", 0))).decode()
            headers = {k.lower(): v for k, v in self.headers.items()}
            log.append({"body": body, "dummy_api_key": headers.get("x-api-key") == launch.DUMMY,
                        "authorization_header": "authorization" in headers})
            events = [{"type": "message_start", "message": {
                "id": "msg_q", "type": "message", "role": "assistant", "model": launch.MODEL, "content": [],
                "stop_reason": None, "stop_sequence": None, "usage": {"input_tokens": 1, "output_tokens": 1}}},
                {"type": "content_block_start", "index": 0, "content_block": {"type": "text", "text": ""}},
                {"type": "content_block_delta", "index": 0, "delta": {"type": "text_delta", "text": "done"}},
                {"type": "content_block_stop", "index": 0},
                {"type": "message_delta", "delta": {"stop_reason": "end_turn", "stop_sequence": None},
                 "usage": {"output_tokens": 1}}, {"type": "message_stop"}]
            self.send_response(200)
            self.send_header("content-type", "text/event-stream")
            self.end_headers()
            self.wfile.write("".join(f"event: {e['type']}\ndata: {json.dumps(e)}\n\n" for e in events).encode())

    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server


def case(name, runtime_root, config_dir, keychain, markers, scratch, sources=""):
    root = Path(scratch) / name
    root.mkdir()
    (root / "task.md").write_text("qualification\n")
    mcp = launch.stage(root / "work/trial", [root / "task.md"], runtime_root, "toolkit", root / "audit")
    home = launch.supervisor_home(root / "home", keychain=keychain)
    launch.no_instruction_ancestors(home)
    out = {"case": name}
    if keychain:
        out["auth"] = launch.subscription_status(home, config_dir)
    log = []
    server = fake(log)
    argv = [f"--setting-sources={sources}" if a == "--setting-sources=" else a
            for a in launch.command(launch.prompt("toolkit"), mcp, 2, launch.MODEL)]
    proc = subprocess.Popen(argv, cwd=home,
                            env=launch.environment(home, config_dir, launch.DUMMY,
                                                   f"http://127.0.0.1:{server.server_address[1]}"),
                            stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            start_new_session=True)
    try:
        proc.communicate(timeout=120)
    except subprocess.TimeoutExpired:
        out["timed_out"] = True
    finally:
        server.shutdown()
        launch.terminate(proc.pid, root / "audit")
    text = "".join(r["body"] for r in log)
    out.update(requests=len(log), body_sha256=[hashlib.sha256(r["body"].encode()).hexdigest() for r in log],
               body_chars=[len(r["body"]) for r in log],
               dummy_api_key=[r["dummy_api_key"] for r in log], authorization_header=[r["authorization_header"] for r in log],
               canary_config=CANARY_CONFIG in text, memory_section="# Memory" in text or "MEMORY.md" in text,
               contents_preamble="Contents of " in text, user_markers_found=sum(m in text for m in markers),
               user_markers_checked=len(markers))
    return out


def main(runtime_root, config_dir, receipt):
    markers = user_markers()
    with tempfile.TemporaryDirectory(prefix="qualify-") as scratch:
        empty = Path(scratch) / "capture-config"
        empty.mkdir()
        planted = Path(scratch) / "planted-config"
        planted.mkdir()
        (planted / "CLAUDE.md").write_text(f"{CANARY_CONFIG}\n")
        launch.verify_config_dir(config_dir)
        cases = [case("capture", runtime_root, empty, False, markers, scratch),
                 case("positive_control", runtime_root, planted, False, markers, scratch, sources="user"),
                 case("supervisor", runtime_root, config_dir, True, markers, scratch)]
        launch.verify_config_dir(config_dir)
    clean = lambda c: c["requests"] > 0 and not (c["canary_config"] or c["contents_preamble"] or c["memory_section"]
                                                 or c["user_markers_found"])
    control = cases[1]
    verdict = {"capture_clean": clean(cases[0]), "supervisor_clean": clean(cases[2]),
               "positive_control_detected": control["canary_config"] and control["contents_preamble"],
               "supervisor_logged_in": bool(cases[2]["auth"]["loggedIn"]),
               "no_credential_header_to_fake_endpoint": not any(h for c in cases for h in c["authorization_header"])}
    Path(receipt).write_text(json.dumps({
        "fingerprints": launch.fingerprints(runtime_root, REPO / "evaluation/pilot/items"),
        "script_sha256": launch.sha(__file__), "config_dir": str(config_dir), "cases": cases, "verdict": verdict,
        "inference_calls": 0, "secrets_or_identity_retained": False}, indent=1) + "\n")
    print(json.dumps(verdict))
    return all(verdict.values())


if __name__ == "__main__":
    sys.exit(0 if main(Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])) else 1)
