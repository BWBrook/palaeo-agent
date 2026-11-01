import collections
import json
from pathlib import Path

repo = Path(__file__).resolve().parents[4]
root = repo / "evaluation/pilot/run-records/pilot-calibration-20261101/trials"
sizes = collections.Counter()
counts = collections.Counter()
for trial_path in sorted(root.glob("T*/trial.json")):
    trial = json.loads(trial_path.read_text())
    if trial["trial"]["arm"] != "toolkit":
        continue
    audit = trial_path.parent / "worker-audit/calls.jsonl"
    for line in audit.read_text().splitlines():
        call = json.loads(line)
        name = call["request"]["tool"]
        counts[name] += 1
        sizes[name] += len(json.dumps(call["result"], sort_keys=True, separators=(",", ":")).encode())

receipt = {
    "scope": "Eight historical toolkit calibration trials; canonical audit result JSON, not wire bytes, model tokens or causal cost attribution",
    "counts": dict(counts),
    "result_json_bytes": dict(sizes),
    "inventory_load_bytes": sizes["supervisor_load_tool_definitions"],
    "excluding_inventory_load_bytes": sum(sizes.values()) - sizes["supervisor_load_tool_definitions"],
    "discovery_and_inspection_bytes": sum(sizes[k] for k in ("discover", "inspect", "study_inspect")),
}
print(json.dumps(receipt, indent=2))
