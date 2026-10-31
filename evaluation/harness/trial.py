"""Historical trial metadata helpers; new live evaluation is suspended.

The original launcher is preserved at freeze commit 5af0041. The counter-review
found credential and shared-state exposure; this module cannot launch workers.
"""

import argparse
import json
from pathlib import Path

from sandbox import profile

ROOT = Path.home() / "palaeo-eval"
RUNTIME = ROOT / "runtime"
BACKENDS = {
    "codex": {"model": "gpt-6.1-sol", "effort": "medium"},
    "claude": {"model": "claude-sonnet-5-5", "effort": None},
}


class LiveEvaluationBlocked(RuntimeError):
    pass


def require_live_evaluation():
    raise LiveEvaluationBlocked(
        "live_evaluation_blocked: the reviewed launcher exposes authentication "
        "and shared agent state to worker tools. Separate these boundaries and "
        "pass new non-disclosing preflights before implementing a new launcher. "
        "See docs/sprint-1-review.md. No override is provided.")


def usage(backend, transcript):
    totals = {}
    for line in transcript.splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if backend == "codex" and event.get("type") == "turn.completed":
            for key, value in event.get("usage", {}).items():
                if isinstance(value, (int, float)):
                    totals[key] = totals.get(key, 0) + value
        if backend == "claude" and event.get("type") == "result":
            for key, value in (event.get("usage") or {}).items():
                if isinstance(value, (int, float)):
                    totals[key] = value
            totals["total_cost_usd"] = event.get("total_cost_usd")
            totals["num_turns"] = event.get("num_turns")
    return totals


COUNTED = {
    "codex": "input_tokens - cached_input_tokens + output_tokens, summed over turn.completed events",
    "claude": "input_tokens + cache_creation_input_tokens + output_tokens from the result event; cache reads reported separately",
}


def counted_tokens(backend, totals):
    if backend == "codex":
        return (totals.get("input_tokens", 0) - totals.get("cached_input_tokens", 0)) + totals.get("output_tokens", 0)
    return totals.get("input_tokens", 0) + totals.get("cache_creation_input_tokens", 0) + totals.get("output_tokens", 0)


def run(materials, arm, backend, record_dir, wall_seconds=300, prompt_override=None):
    require_live_evaluation()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("materials", type=Path)
    parser.add_argument("arm", choices=["direct", "toolkit"])
    parser.add_argument("backend", choices=list(BACKENDS))
    parser.add_argument("record_dir", type=Path)
    parser.add_argument("--wall-seconds", type=int, default=300)
    parser.add_argument("--prompt-file", type=Path)
    parser.parse_args()
    parser.exit(2, "live_evaluation_blocked: see docs/sprint-1-review.md\n")
