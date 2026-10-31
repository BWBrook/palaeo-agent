"""Build the two arm runtimes outside any checkout from the same locked requirements."""

import argparse
import hashlib
import json
import shutil
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
REQUIREMENTS = REPO / "evaluation/runtime/requirements.txt"
PYTHON = "3.12.13"


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def build(root, wheel_dir):
    root = Path(root)
    wheel_dir.mkdir(parents=True, exist_ok=True)
    subprocess.run(["uv", "build", "--wheel", "--out-dir", str(wheel_dir), str(REPO)], check=True,
                   capture_output=True)
    wheels = sorted(wheel_dir.glob("palaeo_agent-*.whl"))
    assert len(wheels) == 1, wheels
    record = {"python": PYTHON, "requirements_sha256": sha256(REQUIREMENTS), "wheel": wheels[0].name,
              "wheel_sha256": sha256(wheels[0]), "arms": {}}
    for arm in ("direct", "toolkit"):
        venv = root / arm
        shutil.rmtree(venv, ignore_errors=True)
        subprocess.run(["uv", "venv", "--python", PYTHON, "--no-project", str(venv)],
                       check=True, capture_output=True)
        py = str(venv / "bin/python")
        subprocess.run(["uv", "pip", "install", "--python", py, "--require-hashes", "-r", str(REQUIREMENTS)],
                       check=True, capture_output=True)
        if arm == "toolkit":
            subprocess.run(["uv", "pip", "install", "--python", py, "--no-deps", str(wheels[0])],
                           check=True, capture_output=True)
        freeze = subprocess.run(["uv", "pip", "freeze", "--python", py], check=True, capture_output=True,
                                text=True).stdout
        probe = subprocess.run([py, "-I", "-c", "import importlib.util as u; print(u.find_spec('palaeo_agent') is not None)"],
                               check=True, capture_output=True, text=True).stdout.strip()
        record["arms"][arm] = {"freeze": freeze.splitlines(), "palaeo_agent_importable": probe == "True"}
    assert record["arms"]["direct"]["palaeo_agent_importable"] is False
    assert record["arms"]["toolkit"]["palaeo_agent_importable"] is True
    toolkit_py = str(root / "toolkit/bin/python")
    discover = subprocess.run([toolkit_py, "-I", "-m", "palaeo_agent", "discover"], check=True,
                              capture_output=True, text=True, cwd="/").stdout
    (root / "palaeo_agent_discover.json").write_text(discover)
    record["discover_sha256"] = hashlib.sha256(discover.encode()).hexdigest()
    (root / "runtime.json").write_text(json.dumps(record, indent=1) + "\n")
    return record


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    args = parser.parse_args()
    out = build(args.root, args.root / "wheel")
    print(json.dumps({k: v for k, v in out.items() if k != "arms"}, indent=1))
