"""Create fresh, symmetric evaluation runtimes without modifying frozen ones."""

import argparse
import hashlib
import json
from pathlib import Path
import subprocess

REPO = Path(__file__).resolve().parents[2]
REQUIREMENTS = Path(__file__).with_name("requirements.txt")


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def command(args):
    return subprocess.run(args, check=True, capture_output=True, text=True).stdout


def describe(python):
    script = '''import hashlib, importlib.metadata as m, importlib.util, json, pathlib, sys
packages = sorted([{"name": d.metadata["Name"], "version": d.version,
 "record_sha256": hashlib.sha256((d.read_text("RECORD") or "").encode()).hexdigest()}
 for d in m.distributions()], key=lambda d: d["name"].lower())
print(json.dumps({"python": sys.version, "executable": sys.executable,
 "base_prefix": sys.base_prefix, "packages": packages,
 "toolkit_importable": importlib.util.find_spec("palaeo_agent") is not None}))'''
    return json.loads(command([str(python), "-I", "-c", script]))


def build(root):
    root = Path(root).resolve()
    root.mkdir(parents=True, exist_ok=False)
    wheel_dir = root / "wheel"
    command(["uv", "build", "--wheel", "--out-dir", str(wheel_dir), str(REPO)])
    wheel, = wheel_dir.glob("*.whl")
    record = {"requirements_sha256": digest(REQUIREMENTS), "wheel_sha256": digest(wheel),
              "wheel": wheel.name, "arms": {}, "status": "building"}
    for arm in ("direct", "toolkit"):
        runtime = root / arm
        command(["uv", "venv", "--python", "3.12.13", "--no-project", str(runtime)])
        python = runtime / "bin/python"
        command(["uv", "pip", "install", "--python", str(python), "--require-hashes", "-r", str(REQUIREMENTS)])
        if arm == "toolkit":
            command(["uv", "pip", "install", "--python", str(python), "--no-deps", str(wheel)])
        record["arms"][arm] = describe(python)
    direct = record["arms"]["direct"]
    toolkit = record["arms"]["toolkit"]
    if direct["toolkit_importable"] or not toolkit["toolkit_importable"]:
        raise RuntimeError("Toolkit import boundary failed")
    without_toolkit = [p for p in toolkit["packages"] if p["name"].lower().replace("_", "-") != "palaeo-agent"]
    identities = lambda packages: [(p["name"], p["version"]) for p in packages]
    if identities(direct["packages"]) != identities(without_toolkit):
        raise RuntimeError("Arm package manifests differ beyond the toolkit")
    record["record_hash_note"] = "Installed RECORD hashes include entry-point shebangs, which differ between arm prefixes; package identities and hash-locked distributions are matched."
    record["status"] = "complete"
    (root / "runtime.json").write_text(json.dumps(record, indent=2) + "\n")
    return record


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path)
    args = parser.parse_args()
    record = build(args.root)
    print(json.dumps({"status": record["status"], "root": str(args.root),
                      "wheel_sha256": record["wheel_sha256"]}))
