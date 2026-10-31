"""macOS sandbox-exec profiles that confine a trial worker from outside its agent CLI."""

import os
import re
from pathlib import Path

HOME = Path.home()
UV_PYTHON = HOME / ".local/share/uv/python"

DENY_READ_COMMON = [
    "/Users/Shared", "/Volumes", "/private/tmp", "/private/var/folders",
    "/opt/homebrew/bin/python3.14", "/opt/homebrew/bin/pip3.14", "/opt/homebrew/Cellar/python@3.14",
    "/opt/homebrew/lib/python3.14", "/opt/homebrew/Frameworks/Python.framework",
    "/opt/homebrew/bin/R", "/opt/homebrew/bin/Rscript", "/opt/homebrew/Cellar/r", "/opt/homebrew/lib/R",
    "/Library/Frameworks/R.framework",
]

# Claude Code authenticates only with its default configuration (keychain-backed), so the
# backend keeps ~/.claude.json and operational state but loses instructions, memory,
# transcripts, skills, plugins and settings.
CLAUDE_DENY = ["CLAUDE.md", "CLAUDE.md.before-wsl-split-dns-20261010", "MACHINE.md", "MACHINE.md.bak-20261024",
               "policy", "machines", "projects", "history.jsonl", "file-history", "skills", "plugins", "bin",
               "githooks", "shell-snapshots", "sessions", "backups", "session-env", "bridge-spawn",
               "settings.json", "settings.json.bak-20261012-github", "statusline.sh"]
CLAUDE_ALLOW_WRITE = [HOME / ".claude", HOME / ".claude.json", HOME / ".claude.json.lock",
                      HOME / "Library/Caches", HOME / "Library/Application Support/Claude"]


def _q(path):
    return '"' + str(path).replace("\\", "\\\\").replace('"', '\\"') + '"'


def profile(*, backend, trial_root, runtime):
    """Deny reads of the user's home except the trial, its runtime and the agent's own needs."""
    trial_root, runtime = Path(trial_root), Path(runtime)
    allow_read = [trial_root, runtime, UV_PYTHON, HOME / "Library/Keychains", HOME / "Library/Preferences"]
    allow_write = [trial_root]
    deny_read = list(DENY_READ_COMMON)
    allow_tmp = []
    if backend == "claude":
        allow_read += [HOME / ".claude", HOME / ".claude.json", HOME / ".claude.json.lock",
                       HOME / "Library/Caches", HOME / "Library/Application Support/Claude"]
        allow_write += CLAUDE_ALLOW_WRITE
        deny_read += [str(HOME / ".claude" / name) for name in CLAUDE_DENY]
        claude_tmp = f"/private/tmp/claude-{os.getuid()}"
        trial_tmp = claude_tmp + "/" + str(trial_root).replace("/", "-")
        allow_tmp = [f"(allow file-read-metadata (literal \"/private/tmp\")) (allow file-read* (literal {_q(claude_tmp)}))",
                     f"(allow file-read* file-write* (regex #\"^{re.escape(trial_tmp)}\"))"]
    elif backend != "codex":
        raise ValueError(backend)
    lines = ["(version 1)", "(allow default)",
             f"(deny file-read* (subpath {_q(HOME)}))",
             f"(allow file-read-metadata (literal {_q(HOME)}) (literal \"/Users\"))"]
    lines += [f"(allow file-read* (subpath {_q(p)}))" for p in allow_read]
    ancestors = sorted({str(a) for p in allow_read for a in Path(p).parents if str(a).startswith(str(HOME))})
    lines += [f"(allow file-read-metadata (literal {_q(a)}))" for a in ancestors]
    lines += [f"(deny file-read* (subpath {_q(p)}))" for p in deny_read]
    lines += [f"(allow file-read* (subpath {_q(trial_root)}))"]
    lines += [line for line in allow_tmp if "file-read-metadata" in line]
    lines += ["(deny file-write* (subpath \"/\"))",
              "(allow file-write* (literal \"/dev/null\") (literal \"/dev/tty\") (literal \"/dev/dtracehelper\")"
              " (regex #\"^/dev/fd/\") (regex #\"^/dev/ttys\"))"]
    lines += [f"(allow file-write* (subpath {_q(p)}))" for p in allow_write]
    lines += [line for line in allow_tmp if "file-write" in line]
    return "\n".join(lines) + "\n"
