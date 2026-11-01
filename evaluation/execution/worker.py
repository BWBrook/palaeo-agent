"""Credential-free, per-call scientific execution on macOS.

The supervisor owns configuration and audit files. Model-controlled paths and
code are handled only by the sandboxed interpreter, never by the supervisor.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import platform
import selectors
import signal
import stat
import subprocess
import threading
import time


class BoundaryError(ValueError):
    pass


def _q(path):
    return json.dumps(str(path))


def _overlap(a, b):
    return a.is_relative_to(b) or b.is_relative_to(a)


def profile(trial_root: Path, runtime: Path, python: Path, trusted_read_roots=()):
    roots = [trial_root, runtime, *trusted_read_roots]
    lines = ["(version 1)", "(deny default)", "(deny process-info* sysctl-read)",
             f"(allow process-exec (literal {_q(python)}) (literal {_q(python.resolve())}))",
             '(allow sysctl-read (sysctl-name "hw.ncpu") (sysctl-name "hw.activecpu") '
             '(sysctl-name "hw.physicalcpu") (sysctl-name "hw.logicalcpu") '
             '(sysctl-name "hw.memsize") (sysctl-name "hw.pagesize") '
             '(sysctl-name "hw.cputype") (sysctl-name "hw.cpusubtype") '
             '(sysctl-name "hw.cpusubfamily") (sysctl-name "kern.osrelease") '
             '(sysctl-name "kern.osproductversion") (sysctl-name "kern.ostype") '
             '(sysctl-name "hw.machine") (sysctl-name "kern.hostname") (sysctl-name "kern.version") '
             '(sysctl-name "kern.osversion") (sysctl-name "security.mac.lockdown_mode_state"))',
             '(allow file-read-data (literal "/"))',
             '(allow file-read* (subpath "/System/Library") (subpath "/usr/lib") '
             '(subpath "/usr/share/zoneinfo"))',
             '(allow file-read* (literal "/dev/null") (literal "/dev/urandom") '
             '(literal "/dev/random") (literal "/private/etc/localtime"))',
             '(allow file-write* (literal "/dev/null"))']
    for root in roots:
        lines.append(f"(allow file-read* (subpath {_q(root)}))")
    ancestors = {p for root in [*roots, python] for p in root.parents}
    pending = [python]
    seen = set()
    while pending:
        candidate = pending.pop()
        if candidate in seen:
            continue
        seen.add(candidate)
        for component in (candidate, *candidate.parents):
            if component.is_symlink():
                target = Path(os.readlink(component))
                target = target if target.is_absolute() else component.parent / target
                ancestors.add(component)
                ancestors.update(target.parents)
                ancestors.add(target)
                pending.append(target)
    for parent in sorted(ancestors):
        lines.append(f"(allow file-read-metadata (literal {_q(parent)}))")
    lines.append(f"(allow file-write* (subpath {_q(trial_root)}))")
    return "\n".join(lines) + "\n"


class Worker:
    def __init__(self, trial_root, runtime, python, log_dir, *, trusted_read_roots=(),
                 timeout_seconds=60, max_output_bytes=65536):
        if platform.system() != "Darwin":
            raise BoundaryError("This tested confinement backend requires macOS sandbox-exec")
        self.trial_root = Path(trial_root).resolve(strict=True)
        self.runtime = Path(runtime).resolve(strict=True)
        self.python = Path(python).absolute()
        self.python.resolve(strict=True)
        self.log_dir = Path(log_dir).resolve()
        self.trusted_read_roots = tuple(Path(p).resolve(strict=True) for p in trusted_read_roots)
        if not self.trial_root.is_dir() or not self.runtime.is_dir():
            raise BoundaryError("Trial and runtime must be directories")
        if not self.python.is_file():
            raise BoundaryError("Interpreter must be an existing file")
        if not any(self.python.resolve().is_relative_to(root) for root in (self.runtime, *self.trusted_read_roots)):
            raise BoundaryError("Interpreter must belong to the runtime or an explicit trusted read root")
        for root in (self.runtime, *self.trusted_read_roots):
            if _overlap(self.trial_root, root) or _overlap(self.log_dir, root):
                raise BoundaryError("Runtime/trusted roots must be disjoint from trial and supervisor records")
        if _overlap(self.log_dir, self.trial_root):
            raise BoundaryError("Supervisor records must be outside the trial")
        if not 0 < timeout_seconds <= 300 or not 1024 <= max_output_bytes <= 1048576:
            raise BoundaryError("Invalid timeout or output bound")
        self.timeout_seconds = timeout_seconds
        self.max_output_bytes = max_output_bytes
        self._lock = threading.Lock()
        self.log_dir.mkdir(parents=True, exist_ok=False)
        self.profile_path = self.log_dir / "worker.sb"
        self.profile_path.write_text(profile(self.trial_root, self.runtime, self.python,
                                             self.trusted_read_roots))
        self.profile_sha256 = hashlib.sha256(self.profile_path.read_bytes()).hexdigest()
        startup = self.log_dir / "startup.json"
        try:
            def fail_walk(error):
                raise error
            for directory, _, filenames in os.walk(self.trial_root, followlinks=False, onerror=fail_walk):
                for filename in filenames:
                    info = (Path(directory) / filename).lstat()
                    if stat.S_ISREG(info.st_mode) and info.st_nlink > 1:
                        raise BoundaryError("Trial files must not share hardlinks with any other path")
            (self.trial_root / ".worker").mkdir(exist_ok=False)
            for name in ("home", "tmp", "cache", "config"):
                (self.trial_root / ".worker" / name).mkdir(exist_ok=False)
        except (OSError, BoundaryError) as exc:
            startup.write_text(json.dumps({"status": "error", "code": "trial_state_not_fresh", "message": str(exc)}) + "\n")
            raise BoundaryError("Trial must be fresh, without shared hardlinks or symlinked worker state") from exc
        startup.write_text(json.dumps({"status": "ready", "profile_sha256": self.profile_sha256}) + "\n")
        self.environment = {
            "HOME": str(self.trial_root / ".worker/home"),
            "TMPDIR": str(self.trial_root / ".worker/tmp"),
            "XDG_CACHE_HOME": str(self.trial_root / ".worker/cache"),
            "XDG_CONFIG_HOME": str(self.trial_root / ".worker/config"),
            "MPLCONFIGDIR": str(self.trial_root / ".worker/config/matplotlib"),
            "PATH": str(self.runtime / "bin"),
            "PYTHONNOUSERSITE": "1", "PYTHONDONTWRITEBYTECODE": "1",
            "OPENBLAS_NUM_THREADS": "1", "OMP_NUM_THREADS": "1",
            "MPLBACKEND": "Agg", "LANG": "en_US.UTF-8",
        }

    def command(self, arguments):
        return ["/usr/bin/sandbox-exec", "-f", str(self.profile_path),
                str(self.python), "-I", *arguments]

    def _audit(self, request, result):
        record = {"time_unix": time.time(), "request": request, "result": result,
                  "profile_sha256": self.profile_sha256}
        with (self.log_dir / "calls.jsonl").open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(record, allow_nan=False) + "\n")

    def reject(self, request, message):
        result = {"status": "error", "code": "invalid_arguments", "message": message}
        with self._lock:
            self._audit(request, result)
        return result

    def run_python(self, arguments, *, stdin="", request=None):
        """Trusted forwarding hook; arguments are supplied by the fixed MCP adapter."""
        request = request or {"tool": "python", "arguments": arguments, "stdin": stdin}
        with self._lock:
            start = time.monotonic()
            buffers = {"stdout": bytearray(), "stderr": bytearray()}
            lengths = {"stdout": 0, "stderr": 0}
            proc = None
            timed_out = False
            try:
                if hashlib.sha256(self.profile_path.read_bytes()).hexdigest() != self.profile_sha256:
                    raise BoundaryError("Supervisor confinement profile changed")
                # A temporary input file is supervisor-owned and inherited as stdin.
                # Worker permissions do not allow opening it by path.
                import tempfile
                with tempfile.TemporaryFile() as input_stream:
                    input_stream.write(stdin.encode())
                    input_stream.seek(0)
                    proc = subprocess.Popen(self.command(arguments), stdin=input_stream,
                                            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                            cwd=self.trial_root, env=self.environment,
                                            start_new_session=True)
                    with (self.log_dir / "pids.jsonl").open("a", encoding="utf-8") as stream:
                        stream.write(json.dumps({"pgid": proc.pid, "time_unix": time.time()}) + "\n")
                    with selectors.DefaultSelector() as selector:
                        for name in buffers:
                            selector.register(getattr(proc, name), selectors.EVENT_READ, name)
                        while selector.get_map():
                            remaining = self.timeout_seconds - (time.monotonic() - start)
                            if remaining <= 0:
                                timed_out = True
                                break
                            for key, _ in selector.select(min(remaining, 0.1)):
                                payload = os.read(key.fileobj.fileno(), 16384)
                                if not payload:
                                    selector.unregister(key.fileobj)
                                    continue
                                name = key.data
                                lengths[name] += len(payload)
                                room = self.max_output_bytes - len(buffers[name])
                                buffers[name].extend(payload[:max(0, room)])
                        if not timed_out:
                            try:
                                proc.wait(timeout=max(0.001, self.timeout_seconds - (time.monotonic() - start)))
                            except subprocess.TimeoutExpired:
                                timed_out = True
                result = {"status": "timed_out" if timed_out else
                          ("ok" if proc.returncode == 0 else "error"),
                          "exit_code": proc.returncode,
                          **{k: bytes(v).decode("utf-8", errors="replace") for k, v in buffers.items()},
                          "output_bytes": lengths,
                          "truncated": {k: lengths[k] > self.max_output_bytes for k in buffers}}
            except (OSError, BoundaryError) as exc:
                result = {"status": "error", "code": "execution_failed", "message": str(exc)}
            finally:
                if proc is not None:
                    try:
                        os.killpg(proc.pid, signal.SIGKILL)
                    except ProcessLookupError:
                        pass
                    proc.wait()
                    proc.stdout.close()
                    proc.stderr.close()
            result["duration_seconds"] = time.monotonic() - start
            self._audit(request, result)
            return result

    def execute(self, code):
        if not isinstance(code, str) or len(code.encode()) > 262144:
            return self.reject({"tool": "worker_execute"}, "code must be a string of at most 262144 bytes")
        return self.run_python(["-c", code], request={"tool": "worker_execute", "code": code})

    def read(self, path, offset=0, limit=32768):
        request = {"tool": "worker_read", "path": path, "offset": offset, "limit": limit}
        if (not isinstance(path, str) or type(offset) is not int or offset < 0 or
                type(limit) is not int or not 1 <= limit <= self.max_output_bytes // 2):
            return self.reject(request, "Invalid path, offset or limit")
        source = (
            "from pathlib import Path; import json\n"
            f"root=Path({str(self.trial_root)!r}); p=(root / {path!r}).resolve()\n"
            "if not p.is_relative_to(root): raise ValueError('path_outside_trial')\n"
            f"with p.open('rb') as f: f.seek({offset}); data=f.read({limit})\n"
            "print(json.dumps({'text':data.decode('utf-8'), 'bytes':len(data), 'offset':"
            f"{offset}" + "}))\n")
        return self.run_python(["-c", source], request=request)

    def write(self, path, content):
        request = {"tool": "worker_write", "path": path, "content": content}
        if not isinstance(path, str) or not isinstance(content, str) or len(content.encode()) > 262144:
            return self.reject({"tool": "worker_write", "path": path}, "Invalid path or content")
        source = (
            "from pathlib import Path; import json\n"
            f"root=Path({str(self.trial_root)!r}); p=(root / {path!r}).resolve()\n"
            "if not p.is_relative_to(root): raise ValueError('path_outside_trial')\n"
            "p.parent.mkdir(parents=True, exist_ok=True)\n"
            f"n=p.write_text({content!r}, encoding='utf-8'); print(json.dumps({{'characters':n}}))\n")
        return self.run_python(["-c", source], request=request)

    def palaeo(self, name, arguments):
        if not isinstance(name, str) or not isinstance(arguments, dict):
            return self.reject({"tool": "palaeo"}, "Invalid palaeo tool call")
        return self.run_python(["-m", "palaeo_agent.mcp_server", "--root", str(self.trial_root),
                                "--call", name], stdin=json.dumps(arguments, allow_nan=False),
                               request={"tool": name, "arguments": arguments})
