"""Synthetic, non-disclosing probes through the actual worker MCP protocol."""

import argparse
import asyncio
import json
from pathlib import Path
import sys


READ_CATEGORIES = ("credentials/auth.json", "Library/Keychains/synthetic.keychain", "Library/Preferences/synthetic.plist",
                   ".codex/state.json", "checkout/answer-key.json", "other-trial/material.txt")


def _deny_code(operation):
    return ("import errno,json\ntry:\n " + operation +
            "\nexcept OSError as e:\n print(json.dumps({'denied':e.errno in (errno.EPERM,errno.EACCES), 'errno':e.errno}))\n"
            "else:\n print(json.dumps({'denied':False}))\n")


async def _session(config_path, callback):
    from mcp.client.session import ClientSession
    from mcp.client.stdio import StdioServerParameters, stdio_client
    params = StdioServerParameters(command=sys.executable,
                                    args=["-m", "evaluation.execution.server", "--config", str(config_path)],
                                    cwd=str(Path(__file__).resolve().parents[2]))
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            return await callback(session)


def _value(result):
    return result.structured_content or json.loads(result.content[0].text)


async def probe_arm(root, runtime, trusted_read_roots, arm, *, python=None):
    arm_root = root / arm
    arm_root.mkdir()
    trial = arm_root / "trial-1"
    trial.mkdir()
    second = arm_root / "trial-2"
    second.mkdir()
    forbidden = arm_root / "forbidden"
    for name in READ_CATEGORIES:
        target = forbidden / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("SYNTHETIC-SECRET-NOT-A-CREDENTIAL\n")
    (trial / "escape").symlink_to(forbidden, target_is_directory=True)
    (trial / "input.txt").write_text("within trial\n")
    python = str(python or runtime / "bin/python")
    config = {"trial_root": str(trial), "runtime": str(runtime), "python": python,
              "log_dir": str(arm_root / "audit-1"), "trusted_read_roots": list(map(str, trusted_read_roots)),
              "timeout_seconds": 3, "max_output_bytes": 65536, "toolkit": arm == "toolkit"}
    config_path = arm_root / "config-1.json"
    config_path.write_text(json.dumps(config))
    checks = []

    async def first(session):
        inventory = await session.list_tools()
        tool_names = [tool.name for tool in inventory.tools]
        (arm_root / "client-tools.json").write_text(json.dumps([t.model_dump(mode="json", by_alias=True) for t in inventory.tools], indent=2))

        async def check(name, code, predicate):
            response = _value(await session.call_tool("worker_execute", {"code": code}))
            checks.append({"name": name, "passed": bool(predicate(response)), "response": response})

        def denied(value):
            return value.get("status") == "ok" and json.loads(value["stdout"]).get("denied") is True

        await check("numerical_execution", "import numpy as np; print(np.linalg.eigvalsh([[1.,2.],[2.,1.]]).tolist())",
                    lambda v: v.get("status") == "ok" and json.loads(v["stdout"]) == [-1.0, 3.0])
        await check("figure_output", "import matplotlib.pyplot as p; p.plot([1,2],[2,4]); p.savefig('figure.png'); print('saved')",
                    lambda v: v.get("status") == "ok" and v["stdout"].strip() == "saved")
        for name in READ_CATEGORIES:
            path = forbidden / name
            await check("deny_read:" + name, _deny_code(f"open({str(path)!r},'rb').read(1)"), denied)
        await check("deny_symlink_read", _deny_code("open('escape/credentials/auth.json','rb').read(1)"), denied)
        await check("deny_outside_write", _deny_code(f"open({str(forbidden / 'persist.txt')!r},'w').write('synthetic')"), denied)
        await check("deny_symlink_write", _deny_code("open('escape/persist-symlink.txt','w').write('synthetic')"), denied)
        await check("deny_other_trial_write", _deny_code(f"open({str(second / 'persist.txt')!r},'w').write('synthetic')"), denied)
        await check("deny_runtime_hardlink", _deny_code(f"import os; os.link({str(runtime / 'pyvenv.cfg')!r},'runtime-link')"), denied)
        await check("deny_forbidden_hardlink", _deny_code(f"import os; os.link({str(forbidden / 'credentials/auth.json')!r},'secret-link')"), denied)
        await check("deny_runtime_mutation", _deny_code(f"open({str(runtime / 'sprint3-probe-write')!r},'w').write('synthetic')"), denied)
        await check("deny_supervisor_log_read", _deny_code(f"open({str(arm_root / 'audit-1/calls.jsonl')!r},'rb').read(1)"), denied)
        await check("deny_network", _deny_code("import socket; socket.create_connection(('127.0.0.1',9), timeout=1)"), denied)
        await check("deny_fork", _deny_code("import os; os.fork()"), denied)
        await check("deny_spawn", _deny_code("import os,sys; os.posix_spawn(sys.executable,[sys.executable,'-c','pass'],{})"), denied)
        await check("deny_process_arguments", "import ctypes,os,json\nlib=ctypes.CDLL(None,use_errno=True)\nmib=(ctypes.c_int*3)(1,49,os.getppid())\nbuf=ctypes.create_string_buffer(262144); size=ctypes.c_size_t(len(buf))\nr=lib.sysctl(mib,3,buf,ctypes.byref(size),None,0)\nprint(json.dumps({'denied':r==-1 and ctypes.get_errno() in (1,13)}))", denied)
        await check("clean_environment", "import os,json; print(json.dumps(sorted(os.environ)))",
                    lambda v: v.get("status") == "ok" and not any("TOKEN" in k or "KEY" in k or "AUTH" in k for k in json.loads(v["stdout"])))
        await check("bounded_output", "print('x'*100000)",
                    lambda v: v.get("status") == "ok" and v["truncated"]["stdout"] is True and len(v["stdout"].encode()) == 65536)
        await check("deadline", "import time; time.sleep(30)", lambda v: v.get("status") == "timed_out")
        write = _value(await session.call_tool("worker_write", {"path": "roundtrip.txt", "content": "round trip"}))
        read = _value(await session.call_tool("worker_read", {"path": "roundtrip.txt"}))
        checks.append({"name": "file_round_trip", "passed": write.get("status") == read.get("status") == "ok" and
                       json.loads(read["stdout"])["text"] == "round trip"})
        bad = _value(await session.call_tool("worker_read", {"path": "../forbidden/credentials/auth.json"}))
        checks.append({"name": "file_tool_escape", "passed": bad.get("status") == "error", "response": bad})
        malformed = _value(await session.call_tool("worker_execute", {"code": "print(1)", "outside": True}))
        checks.append({"name": "malformed_arguments", "passed": malformed.get("status") == "error", "response": malformed})
        await check("trial_local_persistence", "from pathlib import Path; import os; Path(os.environ['HOME'],'persist.txt').write_text('trial1'); print('saved')",
                    lambda v: v.get("status") == "ok")
        return tool_names

    inventory = await _session(config_path, first)
    config.update(trial_root=str(second), log_dir=str(arm_root / "audit-2"))
    second_config = arm_root / "config-2.json"
    second_config.write_text(json.dumps(config))

    async def fresh(session):
        code = "from pathlib import Path; import os,json; print(json.dumps({'persisted':Path(os.environ['HOME'],'persist.txt').exists()}))"
        response = _value(await session.call_tool("worker_execute", {"code": code}))
        checks.append({"name": "fresh_trial_no_state", "passed": response.get("status") == "ok" and
                       json.loads(response["stdout"])["persisted"] is False, "response": response})
        response = _value(await session.call_tool("worker_execute", {"code": _deny_code(f"open({str(trial / 'input.txt')!r},'rb').read(1)")}))
        checks.append({"name": "fresh_trial_cannot_read_previous", "passed": response.get("status") == "ok" and
                       json.loads(response["stdout"])["denied"] is True, "response": response})

    await _session(second_config, fresh)
    return {"arm": arm, "tool_inventory": inventory, "checks": checks,
            "passed": all(item["passed"] for item in checks), "synthetic_only": True,
            "scope": "Actual SDK client initialization/list_tools/call_tool, supervisor dispatcher and confined per-call worker; not proof of supervisor model-visible tool inventory"}


async def run(runtime_root, evidence_root, work_root):
    evidence_root.mkdir(parents=True, exist_ok=False)
    work_root.mkdir(parents=True, exist_ok=False)
    runtime_root = runtime_root.resolve()
    results = []
    for arm in ("direct", "toolkit"):
        py = runtime_root / arm / "bin/python"
        import subprocess
        base = subprocess.check_output([str(py), "-I", "-c", "import sys; print(sys.base_prefix)"], text=True).strip()
        results.append(await probe_arm(work_root, runtime_root / arm, [Path(base).resolve()], arm, python=py))
    receipt = {"status": "passed" if all(r["passed"] for r in results) else "failed", "arms": results,
               "work_root": str(work_root), "runtime_root": str(runtime_root),
               "supervisor_permissions": "Host user access, authentication and network; trusted fixed adapter only",
               "worker_permissions": "Trial read/write; immutable arm/Python runtime and explicit OS read paths; no child processes, network or user state"}
    # Full call evidence is retained outside the worker as well as the compact receipt.
    import shutil
    for arm in ("direct", "toolkit"):
        for name in ("audit-1", "audit-2"):
            shutil.copytree(work_root / arm / name, evidence_root / arm / name)
        shutil.copyfile(work_root / arm / "client-tools.json", evidence_root / arm / "client-tools.json")
    (evidence_root / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
    return receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("runtime_root", type=Path)
    parser.add_argument("evidence_root", type=Path)
    parser.add_argument("--work-root", type=Path, required=True)
    parser.add_argument("--demo", action="store_true", help="Run and reproduce all three scientific methods instead of adversarial probes")
    args = parser.parse_args()
    operation = demonstrate_toolkit if args.demo else run
    result = asyncio.run(operation(args.runtime_root, args.evidence_root, args.work_root))
    counts = {"scientific_runs": len(result["records"])} if args.demo else {"checks": {r["arm"]: len(r["checks"]) for r in result["arms"]}}
    print(json.dumps({"status": result["status"], **counts}))
    return 0 if result["status"] == "passed" else 1


async def demonstrate_toolkit(runtime_root, evidence_root, work_root):
    """Exercise actual science tools and reproduce bundles in a new worker root."""
    import shutil
    import subprocess

    runtime = Path(runtime_root).resolve() / "toolkit"
    python = runtime / "bin/python"
    base = subprocess.check_output([str(python), "-I", "-c", "import sys; print(sys.base_prefix)"], text=True).strip()
    work_root = Path(work_root).resolve()
    work_root.mkdir(parents=True, exist_ok=False)
    trial = work_root / "trial"
    trial.mkdir()
    repo = Path(__file__).resolve().parents[2]
    specs = []
    for source in ("dielasma-l2", "community-llanvirn-raw", "permanova-llanvirn"):
        location = repo / "examples" / f"{source}.json"
        spec = json.loads(location.read_text())
        for field in ("input", "metadata"):
            if spec.get(field):
                original = (location.parent / spec[field]).resolve()
                target = f"{source}-{field}{original.suffix}"
                shutil.copyfile(original, trial / target)
                spec[field] = target
        specs.append(spec)
    config = {"trial_root": str(trial), "runtime": str(runtime), "python": str(python),
              "log_dir": str(work_root / "audit-original"), "trusted_read_roots": [str(Path(base).resolve())],
              "timeout_seconds": 60, "max_output_bytes": 65536, "toolkit": True}
    cfg = work_root / "config-original.json"
    cfg.write_text(json.dumps(config))
    records = []

    async def original(session):
        for spec in specs:
            result = _value(await session.call_tool("palaeo_run", {"spec": spec}))
            if result.get("status") != "complete":
                raise RuntimeError(json.dumps(result))
            records.append(result)
        refusal = _value(await session.call_tool("palaeo_validate", {"spec": {**specs[-1], "design": "repeated"}}))
        if refusal.get("status") != "error":
            raise RuntimeError("Expected unsupported-design refusal")
        return refusal

    refusal = await _session(cfg, original)
    fresh = work_root / "fresh-trial"
    shutil.copytree(trial, fresh, ignore=shutil.ignore_patterns(".worker"))
    config.update(trial_root=str(fresh), log_dir=str(work_root / "audit-fresh"))
    cfg2 = work_root / "config-fresh.json"
    cfg2.write_text(json.dumps(config))

    async def reproduce(session):
        for record in records:
            bundle_path = Path(record["run_dir"])
            bundle = str(bundle_path.relative_to(trial)) if bundle_path.is_absolute() else str(bundle_path)
            result = _value(await session.call_tool("palaeo_reproduce", {"bundle": bundle, "output": "reproduced"}))
            if result.get("status") != "reproduced":
                raise RuntimeError(json.dumps(result))
            record["fresh_reproduction"] = result

    await _session(cfg2, reproduce)
    evidence_root = Path(evidence_root)
    evidence_root.mkdir(parents=True, exist_ok=False)
    for name in ("audit-original", "audit-fresh"):
        shutil.copytree(work_root / name, evidence_root / name)
    receipt = {"status": "passed", "records": records, "refusal": refusal,
               "fresh_process": "New MCP supervisor and fresh copied trial; each scientific call also has a new sandboxed Python process",
               "runtime": str(runtime), "work_root": str(work_root), "model_calls": 0}
    (evidence_root / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
    return receipt


if __name__ == "__main__":
    raise SystemExit(main())
