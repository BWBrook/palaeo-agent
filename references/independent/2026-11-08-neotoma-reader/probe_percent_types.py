"""Probe structured refusals for nonnumeric percentage values."""

import hashlib
import json
from pathlib import Path
import sys

import palaeo_agent as pa


root = Path(sys.argv[1]).resolve()
root.mkdir(parents=True, exist_ok=False)
results = []
for label, value in (("null", None), ("object", {}), ("list", [])):
    datum = {"variablename": "Pinus", "value": value, "units": "percent",
             "element": "pollen", "ecologicalgroup": "TRSH", "taxonid": 1}
    source = {"data": [{"site": {"siteid": 1, "sitename": "Fixture",
              "collectionunit": {"collectionunitid": 1, "dataset": {
                  "datasetid": 1, "samples": [{"sampleid": 1, "datum": [datum], "ages": []}]}}}}]}
    path = root / (label + ".json")
    path.write_text(json.dumps(source))
    spec = {"source": str(path), "source_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "datasets": "all", "units": "percent", "elements": ["pollen"],
            "ecological_groups": ["TRSH"], "absent_taxa": "zero", "row_order": "source"}
    try:
        result = pa.neotoma_extract(spec, root / "bundles")
        results.append({"case": label, "status": result["status"]})
    except Exception as exc:
        results.append({"case": label, "exception": type(exc).__name__,
                        "code": getattr(exc, "code", None), "message": str(exc)})
(root / "receipts.json").write_text(json.dumps(results, indent=2) + "\n")
print(json.dumps(results, indent=2))
