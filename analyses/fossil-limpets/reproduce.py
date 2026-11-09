"""Check portable study reproduction and fresh-process numerical exports."""

import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]

CHILD = """
import hashlib, json, pathlib, sys
from unittest.mock import patch
import palaeo_agent as pa
old, new, forbidden = map(pathlib.Path, sys.argv[1:])
original_open = pathlib.Path.open
attempts = []
def guarded_open(path, *args, **kwargs):
    if path.resolve().is_relative_to(forbidden):
        attempts.append(str(path))
        raise OSError('Original application paths deliberately blocked')
    return original_open(path, *args, **kwargs)
with patch.object(pathlib.Path, 'open', guarded_open):
    try:
        (forbidden / 'measurements.tsv').read_bytes()
    except OSError:
        pass
    else:
        raise AssertionError('Original-path guard failed')
    attempts.clear()
    outcome = pa.reproduce_study(old, new)
    assert outcome['status'] == 'reproduced', outcome
    assert not attempts
    first = json.loads((old / 'manifest.json').read_bytes())
    second = json.loads((new / 'manifest.json').read_bytes())
    hashes = {}
    for name, item in first['runs'].items():
        a = (old / item['run_dir'] / 'results.json').read_bytes()
        b = (new / second['runs'][name]['run_dir'] / 'results.json').read_bytes()
        assert a == b, name
        hashes[name] = hashlib.sha256(b).hexdigest()
print(json.dumps({'status': outcome['status'], 'derived_identical': outcome['derived_identical'],
                  'original_path_probe_refused': True, 'original_path_read_attempts_during_replay': len(attempts),
                  'byte_identical_child_results': hashes}))
"""


def main():
    provenance = json.loads((HERE / "provenance.json").read_text())
    original = HERE / provenance["study_dir"]
    exports = ["results.json", "api-pairs.csv", "api-scalars.csv"]
    before = {name: (HERE / name).read_bytes() for name in exports}
    with tempfile.TemporaryDirectory(prefix="palaeo-limpet-replay-") as temp:
        root = Path(temp)
        shutil.copytree(original, root / "copied-study")
        completed = subprocess.run([sys.executable, "-c", CHILD, str(root / "copied-study"),
                                    str(root / "reproduced-study"), str(HERE)],
                                   cwd=temp, check=True, capture_output=True, text=True)
        portable = json.loads(completed.stdout)
    target = Path(tempfile.mkdtemp(prefix="runs-export-", dir=HERE)) / "study"
    subprocess.run([sys.executable, str(HERE / "analysis.py"), "--output", str(target)],
                   cwd=REPO, check=True, capture_output=True, text=True)
    assert all((HERE / name).read_bytes() == data for name, data in before.items())
    receipt = {"portable_study": portable, "fresh_process_exports_identical": True,
               "exports": [{"file": name, "sha256": hashlib.sha256(data).hexdigest()} for name, data in before.items()],
               "source_study": provenance["study_dir"], "export_replay_study": str(target.relative_to(HERE)),
               "scope": "Byte-identical numerical results and preparation; figures and scientific interpretation are not validated"}
    (HERE / "reproduction-check.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps(receipt, indent=2))


if __name__ == "__main__":
    main()
