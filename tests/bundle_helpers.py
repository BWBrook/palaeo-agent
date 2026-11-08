import hashlib
import json
from pathlib import Path


def rehash(run_dir, name):
    manifest_path = Path(run_dir) / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    data = (Path(run_dir) / name).read_bytes()
    manifest["files"][name].update(sha256=hashlib.sha256(data).hexdigest(), bytes=len(data))
    manifest_path.write_text(json.dumps(manifest, indent=2))
