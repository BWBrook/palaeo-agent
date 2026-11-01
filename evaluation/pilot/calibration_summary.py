"""Calibration summary against the freeze rules (docs/sprints-3-4-proposal.md, calibration and envelope).

- Ceiling rule: if the direct arm gets at least 7 of 8 calibration traps
  acceptable, the families are revised before freeze.
- Working analyst ceiling: 1.5 x the median counted tokens per trial x 96,
  never above the 5,000,000 Sonnet authorisation.
- Provisional (adjudication-pending) outcomes are listed, never silently
  counted as acceptable.

    python evaluation/pilot/calibration_summary.py OUT_DIR > summary.json
"""

import json
from pathlib import Path
import statistics
import sys

AUTHORISED = 5_000_000


def main(out_dir):
    trials = []
    for path in sorted((Path(out_dir) / "trials").glob("*/trial.json")):
        r = json.loads(path.read_text())
        s = r.get("score", {})
        trials.append({"trial": r["trial"]["trial_id"], "item": r["trial"]["item"], "arm": r["trial"]["arm"],
                       "family": r["trial"]["family"], "stratum": s.get("stratum"), "complete": r.get("complete"),
                       "termination": r.get("termination"), "outcome": s.get("outcome"), "pitfall": s.get("pitfall"),
                       "acceptable": s.get("acceptable"), "provisional": s.get("provisional", False),
                       "counted_tokens": r.get("counted_tokens"), "cache_read_tokens": r.get("cache_read_tokens"),
                       "worker_calls": r.get("reconciliation", {}).get("worker"),
                       "client_refusals": r.get("reconciliation", {}).get("client_refusal")})
    arms = {}
    for arm in ("direct", "toolkit"):
        rows = [t for t in trials if t["arm"] == arm]
        arms[arm] = {"trials": len(rows), "complete": sum(bool(t["complete"]) for t in rows),
                     "acceptable": sum(bool(t["acceptable"]) and not t["provisional"] for t in rows),
                     "acceptable_provisional": sum(bool(t["acceptable"]) and t["provisional"] for t in rows),
                     "median_counted_tokens": statistics.median([t["counted_tokens"] for t in rows
                                                                 if t["counted_tokens"] is not None] or [0])}
    counted = [t["counted_tokens"] for t in trials if t["counted_tokens"] is not None]
    median = statistics.median(counted) if counted else None
    direct = arms["direct"]
    return {"trials": trials, "arms": arms,
            "ceiling_rule": {"direct_acceptable_upper": direct["acceptable"] + direct["acceptable_provisional"],
                             "direct_acceptable_lower": direct["acceptable"], "threshold": 7,
                             "revise_families": direct["acceptable"] >= 7,
                             "undetermined_until_adjudication": direct["acceptable"] < 7 <=
                             direct["acceptable"] + direct["acceptable_provisional"]},
            "tokens": {"total_counted": sum(counted), "median_counted": median,
                       "working_analyst_ceiling": min(AUTHORISED, round(1.5 * median * 96)) if median else None}}


if __name__ == "__main__":
    print(json.dumps(main(sys.argv[1]), indent=1))
