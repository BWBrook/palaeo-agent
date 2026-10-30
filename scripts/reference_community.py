"""Regenerate the base-R library reference and record its provenance."""

import hashlib
import json
from pathlib import Path
import subprocess
import tempfile

root = Path(__file__).resolve().parents[1]
source = root / "benchmarks/past/legacy-data/llanvirn.dat"
script = root / "scripts/reference_community.R"
destination = root / "benchmarks/past/references/community-base-r.json"
with tempfile.TemporaryDirectory() as temp:
    output = Path(temp) / "reference.json"
    subprocess.run(["Rscript", str(script), str(source), str(output)], check=True)
    record = json.loads(output.read_text())
record["input"] = source.relative_to(root).as_posix()
record["input_sha256"] = hashlib.sha256(source.read_bytes()).hexdigest()
record["reference_script_sha256"] = hashlib.sha256(script.read_bytes()).hexdigest()
record["generator_sha256"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
destination.write_text(json.dumps(record, indent=2) + "\n")
print(f"Wrote {len(record['cases'])} base-R comparisons to {destination.relative_to(root)}")
