"""Stage 2, step 1: run the frozen Lake Selina specs through the Palaeo-Agent API. Run: uv run analyses/lake-selina/run_api.py

Writes run bundles under runs/ (gitignored, regenerable) and runs/index.json with each bundle path.
"""

import json
import os
import time
from pathlib import Path

import palaeo_agent as pa

HERE = Path(__file__).resolve().parent
RUNS = HERE / "runs"


def main():
    design = json.loads((HERE / "design.json").read_text())
    os.chdir(HERE)
    RUNS.mkdir(exist_ok=True)
    index = {}
    for name, spec in design["specs"].items():
        start = time.time()
        out = pa.run(spec, RUNS / name)
        run_dir = out["run_dir"] if isinstance(out, dict) else out
        inspected = pa.inspect_run(run_dir)
        index[name] = {"run_dir": str(Path(run_dir).relative_to(HERE)), "seconds": round(time.time() - start, 1),
                       "status": inspected.get("status", "inspected")}
        print(name, index[name], flush=True)
    rel, raw = (HERE / index["community_relative_braycurtis"]["run_dir"],
                HERE / index["community_raw_braycurtis"]["run_dir"])
    comparison = pa.compare_community_runs(rel, raw, RUNS / "comparisons")
    index["compare_relative_vs_raw"] = {"comparison_dir": str(Path(comparison["comparison_dir"]).relative_to(HERE))}
    (RUNS / "index.json").write_text(json.dumps(index, indent=1) + "\n")


if __name__ == "__main__":
    main()
