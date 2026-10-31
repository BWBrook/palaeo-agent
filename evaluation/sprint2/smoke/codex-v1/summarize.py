"""Recompute descriptive smoke summaries; no package import or model calls."""

import hashlib
import json
import re
import statistics
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCE_COMMIT = "1093bb0c4a4d7ef556658418210fae3bcac79881"
FREEZE_COMMIT = "b670270"
REPAIR_COMMIT = "1943c30"


def save(name, value):
    (HERE / name).write_text(json.dumps(value, indent=2) + "\n")


def completed_commands(path):
    events = []
    thread_ids = []
    for n, line in enumerate(path.read_text().splitlines(), 1):
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if event.get("type") == "thread.started":
            thread_ids.append(event.get("thread_id"))
        item = event.get("item", {})
        if event.get("type") == "item.completed" and item.get("type") == "command_execution":
            events.append({"transcript_line": n, "command": item.get("command", ""), "exit_code": item.get("exit_code")})
    return events, thread_ids


def summarize():
    scores = json.loads((HERE / "scores.json").read_text())
    plan = json.loads((HERE / "plan.json").read_text())
    records, fidelity, leakage = [], [], []
    all_threads = []
    for path in sorted((HERE / "trials").iterdir()):
        meta = json.loads((path / "trial.json").read_text())
        answer = json.loads((path / "workspace/answer.json").read_text())
        commands, threads = completed_commands(path / "transcript.jsonl")
        all_threads.extend(threads)
        numeric = [event for event in commands if event["exit_code"] == 0
                   and re.search(r"-m\s+palaeo_agent\s+run\s+(?!\-\-help)", event["command"])]
        fetch = [event for event in commands if re.search(
            r"\bcurl\b|\bwget\b|requests\.(get|post)|urllib\.request|httpx\.|https?://", event["command"])]
        spawn = [event for event in commands if re.search(r"\b(codex\s+exec|claude\s+-p)\b", event["command"])]
        raw_flags = json.loads((path / "leak_scan.json").read_text())
        urls = sorted(set(re.findall(r"https?://[^\\\s\"<>]+", (path / "transcript.jsonl").read_text())))
        script_candidates = []
        for script in sorted((path / "workspace").rglob("*.py")):
            for line_number, line in enumerate(script.read_text().splitlines(), 1):
                if re.search(r"import (requests|urllib|httpx|socket)|from (requests|urllib|httpx|socket)|\b(curl|wget)\b|\b(codex\s+exec|claude\s+-p)\b", line):
                    script_candidates.append({"file": str(script.relative_to(path / "workspace")),
                                              "line": line_number, "text": line})
        stopped = answer["status"] == "stopped"
        fidelity.append({
            "trial": path.name, "arm": meta["arm"], "answer_status": answer["status"],
            "toolkit_numeric_run_observed": bool(numeric), "numeric_run_evidence": numeric,
            "toolkit_role": ("CLI numerical execution plus saved bundle" if numeric else
                             "discovery/help only; reasoned stop before inference" if meta["arm"] == "toolkit" else
                             "not available under runtime preflight; direct local script"),
            "nonzero_command_exits": sum(event["exit_code"] != 0 for event in commands),
            "command_count": len(commands), "reasoned_design_stop": stopped,
            "scope": "Successful command execution and saved files distinguish invocation from availability. Shell corrections inside a trial are not controller/model trial retries.",
        })
        leakage.append({
            "trial": path.name, "raw_flags": raw_flags, "distinct_printed_urls": urls,
            "network_fetch_command_candidates": fetch, "child_agent_command_candidates": spawn,
            "saved_script_network_or_child_agent_candidates": script_candidates,
            "review": ("Only documentation/reference URLs printed by discovery and result output; no fetch command observed."
                       if raw_flags else "No frozen scanner flags."),
            "confirmed_protected_read_or_key_leak": False,
            "limit": "Finite transcript/script review is not proof of no leakage or network activity. Network isolation was not established.",
        })
        records.append({"trial": path.name, "arm": meta["arm"], "counted_tokens": meta["counted_tokens"],
                        "elapsed_seconds": meta["elapsed_seconds"], "termination": meta["termination"],
                        "returncode": meta["returncode"], "usage": meta["usage"], "stopped": stopped,
                        "requested_model": meta["model"], "requested_effort": meta["effort"],
                        "cli_version": meta["cli_version"]})
    assert len(records) == len(scores) == 12
    assert all(record["termination"] == "exited" and record["returncode"] == 0 for record in records)
    assert all(row["outcome"] == "correct" for row in scores)
    assert all(not row["network_fetch_command_candidates"] and not row["child_agent_command_candidates"]
               and not row["saved_script_network_or_child_agent_candidates"] for row in leakage)
    assert all(set(row["raw_flags"]) <= {"network_fetch"} for row in leakage)
    arms = {}
    for arm in ("direct", "toolkit"):
        rows = [record for record in records if record["arm"] == arm]
        arm_scores = [row for row in scores if row["arm"] == arm]
        numeric = [record for record in rows if not record["stopped"]]
        arms[arm] = {
            "trials": len(rows), "correct_primary": sum(row["outcome"] == "correct" for row in arm_scores),
            "completed_numerical_cases": len(numeric), "reasoned_design_stops": sum(record["stopped"] for record in rows),
            "counted_tokens": sum(record["counted_tokens"] for record in rows),
            "mean_counted_tokens": statistics.mean(record["counted_tokens"] for record in rows),
            "elapsed_seconds_sum": sum(record["elapsed_seconds"] for record in rows),
            "mean_elapsed_seconds": statistics.mean(record["elapsed_seconds"] for record in rows),
            "numerical_cases_mean_counted_tokens": statistics.mean(record["counted_tokens"] for record in numeric),
            "numerical_cases_mean_elapsed_seconds": statistics.mean(record["elapsed_seconds"] for record in numeric),
            "evidence_scores": [row["evidence"]["score"] for row in arm_scores],
            "mean_evidence_score": statistics.mean(row["evidence"]["score"] for row in arm_scores),
            "evidence_environment_check_failures": [row["trial"] for row in arm_scores
                                                     if not row["evidence"]["checks"]["environment_recorded"]],
            "caveat_counts": [row["caveats"] for row in arm_scores],
            "caveat_note": "Counts include required independence/exchangeability assumptions and legitimate limitations; they are not automatically spurious warnings.",
        }
    totals = {key: sum(record["usage"].get(key, 0) for record in records)
              for key in ("input_tokens", "cached_input_tokens", "output_tokens", "reasoning_output_tokens")}
    summary = {
        "version": plan["version"], "live_source_commit": SOURCE_COMMIT, "freeze_commit": FREEZE_COMMIT,
        "subsequent_numerically_validated_repair_commit": REPAIR_COMMIT,
        "freeze_sha256": plan["freeze_sha256"], "postrun_frozen_files_verified_before_source_repair": 69,
        "trials_completed": 12, "trials_planned": 12, "controller_retries": 0, "timeouts": 0,
        "primary_correct": 12, "completed_numerical_cases": 10, "reasoned_design_stops": 2,
        "counted_tokens": sum(record["counted_tokens"] for record in records),
        "token_ceiling": plan["token_ceiling"], "counted_definition": plan["counted_tokens"],
        "reported_usage": totals, "elapsed_seconds_sum": sum(record["elapsed_seconds"] for record in records),
        "distinct_thread_ids": len(set(all_threads)), "requested_model": plan["model"], "requested_effort": plan["effort"],
        "model_attestation_limit": "The command and frozen configuration request this model/effort. Stream events do not independently attest an internal model build.",
        "cli_versions": sorted({record["cli_version"] for record in records}), "arms": arms,
        "toolkit_numerical_invocation_trials": sum(row["toolkit_numeric_run_observed"] for row in fidelity),
        "toolkit_discovery_only_design_stops": sum(row["arm"] == "toolkit" and row["reasoned_design_stop"] for row in fidelity),
        "remaining_temporary_trial_directories": len(list((Path.home() / "palaeo-eval/sprint2/t").glob("*"))),
        "scanner_flagged_trials": sum(bool(row["raw_flags"]) for row in leakage),
        "scanner_network_url_matches": sum(row["raw_flags"].get("network_fetch", 0) for row in leakage),
        "confirmed_observed_key_or_source_leaks": 0,
        "limitations": [
            "Development smoke: six synthetic low-dimensional items, one trial per item-arm, one requested model/effort; no efficacy estimate.",
            "All numerical items use two taxa and two groups, exact enumeration and F no larger than 1470; no broad numerical coverage is implied.",
            "G3 measures response to a supplied interpretation claim, not independent spontaneous scientific interpretation.",
            "Design independence is supplied by the task description, not statistically verified by the package.",
            "The outer sandbox preflight passed protected-read/write and arm-import checks, but network isolation and absence of every possible leak were not established.",
            "A later independent stress test found a high-F three-group tie-accumulation defect in the live source. A subsequent stable-summation repair is outside these live trials; no claim is made that the repaired wheel received this smoke.",
            "Token totals are observed usage under existing Codex authentication; no dollar-cost estimate is inferred.",
            "The frozen evidence checklist requires a recorded NumPy version even for standard-library-only arithmetic or a reasoned design stop; its environment check must be interpreted separately from reproducibility of the executed code.",
        ],
    }
    adjudication = {
        "reviewer_role": "The sprint-2 evaluation delegate that authored this development bank; cross-review remains separate.",
        "automatic_scores_unchanged": True,
        "cases": [{"trial": name, "automatic_outcome": "correct", "review_outcome": "correct",
                   "evidence": "Answer is stopped with empty results and identifies site_reef_01/site_lagoon_01, dependent subsamples and one site per facies. Saved executed analysis.py validates the design and does not calculate PERMANOVA or dispersion.",
                   "toolkit_role": role} for name, role in (
                       ("04-G2-trap-toolkit", "Discovery/help invoked; no numeric engine invocation."),
                       ("12-G2-trap-direct", "Direct validation script; no numeric inference."))],
        "interpretation_review": "All four G3 answers correctly qualify group association and separate descriptive centroid spread from proof of a pure location effect. Both G1-trap answers preserve ID alignment: direct analysis.py constructs metadata lookup by sample_id; toolkit run saves aligned metadata and groups. This supports these specific process claims, not every assertion in an answer.",
    }
    save("costs.json", {"totals": totals, "counted_tokens": summary["counted_tokens"], "token_ceiling": summary["token_ceiling"],
                        "elapsed_seconds_sum": summary["elapsed_seconds_sum"], "arms": arms, "trials": records})
    save("fidelity.json", fidelity)
    save("leak-adjudication.json", leakage)
    save("adjudication.json", adjudication)
    save("summary.json", summary)
    report = f"""# Sprint-2 frozen Codex feasibility smoke

Twelve of twelve planned trials completed normally: **12 automatic primary
scores correct**, comprising ten completed numerical cases and two reasoned
stops on the dependent design. There were no timeouts, controller retries,
replacement trials or ceiling-stopped launches. Both keyword-based G2 stop
scores were reviewed against the answers and executed saved scripts; the
automatic scores remain unchanged.

Live source: `{SOURCE_COMMIT}`. Instrument freeze: `{FREEZE_COMMIT}`.
The model/effort requested in every command was `gpt-6.1-sol`, medium; observed
CLI version was `codex-cli 0.166.0`. The stream does not independently attest an
internal model build. All 69 frozen file hashes still matched immediately after
the controller finished, before the subsequent source repair.

| Observed measure | Direct | Toolkit |
| --- | ---: | ---: |
| Correct primary scores | 6/6 | 6/6 |
| Completed numerical cases | 5 | 5 |
| Reasoned dependent-design stops | 1 | 1 |
| Counted tokens | {arms['direct']['counted_tokens']:,} | {arms['toolkit']['counted_tokens']:,} |
| Mean counted tokens/trial | {arms['direct']['mean_counted_tokens']:,.1f} | {arms['toolkit']['mean_counted_tokens']:,.1f} |
| Mean elapsed seconds/trial | {arms['direct']['mean_elapsed_seconds']:.1f} | {arms['toolkit']['mean_elapsed_seconds']:.1f} |
| Mean frozen evidence-checklist score | {arms['direct']['mean_evidence_score']:.3f} | {arms['toolkit']['mean_evidence_score']:.3f} |

Total counted usage was **{summary['counted_tokens']:,}** uncached input plus
output tokens, below the 300,000 launch-stop ceiling. Aggregate trial elapsed
time was {summary['elapsed_seconds_sum']:.1f} seconds. Full input, cached-input
and output usage is retained in costs.json; no dollar estimate is inferred.

Actual successful `palaeo_agent run` invocation is visible in all five toolkit
numerical trials, with saved bundles. The toolkit dependent-design trial used
discovery/help and then stopped before inference. Availability alone is not
counted as numerical API use. Both arms' design stops identify the shared sites
and lack of independent facies replication. All twelve passed the saved-code,
input-hash and answer-validity checklist checks. The environment check passed
in one direct and five toolkit trials. It requires Python and NumPy versions,
including for scripts using only standard-library rational arithmetic and for
stops before numerical computation; this secondary measure does not directly
establish a general reproducibility advantage. Individual checks are retained
in scores.json.
Required assumptions and legitimate limitations are included in caveat counts;
those counts are not automatically spurious warnings.

The scanner flagged six toolkit transcripts, with 42 URL matches. Command and
saved-script review found printed documentation/reference URLs, no fetch or
install commands, and no observed child-agent invocation or protected key/source
read. Original scanner flags are preserved separately from this adjudication.
Preflight demonstrated denied reads of both banks' keys, checkout/source,
instructions, other-arm runtime and canaries, plus denied outside writes. The
toolkit imported only from its arm's wheel installation. Network isolation and
absence of every possible leak were not established.

These are development items: two taxa, two groups, exact enumeration and maximum
F=1470, with one trial per item-arm. G3 assesses a supplied draft claim. This is
evidence that the instrument and supported workflows functioned in these cases,
not an efficacy estimate or broad validation of PAST compatibility.

A later independent stress test identified a high-F, three-group floating-point
tie-accumulation defect in this live source. The separately prepared
stable-summation repair was applied only after the smoke finished. **The repaired
wheel at `{REPAIR_COMMIT}` did not receive these live trials**. Its subsequent
numerical validation is separate, and this smoke does not validate it.

Recompute summaries with `python evaluation/sprint2/smoke/codex-v1/summarize.py`.
Recompute frozen automatic scores with `python evaluation/sprint2/score.py
evaluation/sprint2/smoke/codex-v1`. No model calls are made by either command.
"""
    (HERE / "RESULTS.md").write_text(report)
    return summary


if __name__ == "__main__":
    print(json.dumps(summarize(), indent=2))
