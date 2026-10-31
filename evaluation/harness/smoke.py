"""Run a frozen smoke plan sequentially, with a token stop ceiling and no retries."""

import argparse
import json
import random
import re
from pathlib import Path

import trial

EVAL = Path(__file__).resolve().parents[1]
LEAK_PATTERNS = {
    "development_checkout": r"/Users/[^/\s]+/work",
    "agent_config": r"\.claude/|\.codex/",
    "other_trial": r"palaeo-eval/t/",
    "package_install": r"\bpip3? install\b|\buv (pip|add|tool)\b|\bconda install\b",
    "network_fetch": r"\bcurl\b|\bwget\b|https?://(?!json-schema\.org)",
    "blocked_access": r"Operation not permitted",
}


def make_plan(path, backend, seed, ceiling, version):
    items = sorted(p.parent.name for p in (EVAL / "items").glob("*/key.json")
                   if json.loads(p.read_text())["smoke"])
    order = [(item, arm) for item in items for arm in ("direct", "toolkit")]
    random.Random(seed).shuffle(order)
    plan = {"version": version, "backend": backend, **trial.BACKENDS[backend], "wall_seconds": 300,
            "token_ceiling": ceiling, "counted_tokens": trial.COUNTED[backend], "seed": seed,
            "order": [{"item": i, "arm": a} for i, a in order]}
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(plan, indent=1) + "\n")
    return plan


def leak_scan(record, trial_id):
    text = (record / "transcript.jsonl").read_text() + (record / "stderr.txt").read_text()
    hits = {}
    for name, pattern in LEAK_PATTERNS.items():
        found = [m.group(0) for m in re.finditer(pattern, text)]
        if name == "other_trial":
            found = [f for f, m in zip(found, re.finditer(r"palaeo-eval/t/(\w+)", text)) if m.group(1) != trial_id]
        if found:
            hits[name] = len(found)
    return hits


def run(plan_path):
    plan = json.loads(plan_path.read_text())
    out = plan_path.parent / "trials"
    spent, log = 0, []
    for n, step in enumerate(plan["order"], 1):
        record = out / f"{n:02d}-{step['item']}-{step['arm']}"
        if record.exists():
            meta = json.loads((record / "trial.json").read_text())
            spent += meta["counted_tokens"]
            continue
        if spent >= plan["token_ceiling"]:
            log.append({"step": n, **step, "status": "not_run_token_ceiling"})
            continue
        meta = trial.run(EVAL / "items" / step["item"] / "materials", step["arm"], plan["backend"], record,
                         plan["wall_seconds"])
        if (meta["counted_tokens"] == 0 and meta["elapsed_seconds"] < 30
                and not (record / "workspace/answer.json").exists()):
            first = record.rename(record.with_name(record.name + "-infra-failure"))
            print(json.dumps({"step": n, "infrastructure_failure": first.name}), flush=True)
            meta = trial.run(EVAL / "items" / step["item"] / "materials", step["arm"], plan["backend"], record,
                             plan["wall_seconds"])
        scan = leak_scan(record, meta["trial_id"])
        (record / "leak_scan.json").write_text(json.dumps(scan, indent=1) + "\n")
        spent += meta["counted_tokens"]
        log.append({"step": n, **step, "status": "run", "termination": meta["termination"],
                    "elapsed_seconds": meta["elapsed_seconds"], "counted_tokens": meta["counted_tokens"],
                    "cumulative_counted_tokens": spent, "leak_scan": scan})
        print(json.dumps(log[-1]), flush=True)
    (plan_path.parent / "run_log.json").write_text(json.dumps(log, indent=1) + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("plan")
    p.add_argument("path", type=Path)
    p.add_argument("--backend", required=True, choices=list(trial.BACKENDS))
    p.add_argument("--seed", type=int, required=True)
    p.add_argument("--ceiling", type=int, required=True)
    p.add_argument("--version", required=True)
    r = sub.add_parser("run")
    r.add_argument("path", type=Path)
    args = parser.parse_args()
    if args.cmd == "plan":
        print(json.dumps(make_plan(args.path, args.backend, args.seed, args.ceiling, args.version), indent=1))
    else:
        run(args.path)
