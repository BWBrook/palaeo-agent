"""Portable fresh-process reproduction with the original application files blocked."""

import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

from reproduce import CHILD

HERE = Path(__file__).resolve().parent


def main():
    provenance = json.loads((HERE / "provenance-amended.json").read_text())
    original = HERE / provenance["study_dir"]
    with tempfile.TemporaryDirectory(prefix="palaeo-limpet-amended-replay-") as temp:
        root = Path(temp)
        shutil.copytree(original, root / "copied-study")
        completed = subprocess.run([sys.executable, "-c", CHILD, str(root / "copied-study"),
                                    str(root / "reproduced-study"), str(HERE)],
                                   cwd=temp, check=True, capture_output=True, text=True)
        portable = json.loads(completed.stdout)
    names = ["results-amended.json", "bootstrap-amended.csv", "inference-amended.csv"]
    receipt = {"portable_study": portable, "freeze_commit": provenance["freeze_commit"],
        "source_study": provenance["study_dir"],
        "exports": [{"file": name, "sha256": hashlib.sha256((HERE / name).read_bytes()).hexdigest()} for name in names],
        "scope": "Copied study reproduces all three complete native results byte for byte in a fresh worker; original application paths blocked; scientific assumptions not validated"}
    (HERE / "reproduction-check-amended.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps(receipt, indent=2))


if __name__ == "__main__":
    main()
