"""Pilot scorer: the revised scorer plus the pilot-v3 key fields.

- acceptable_alternatives: a stopped answer that names the listed issue is
  correct_unresolved (P04-trap).
- disclosure_tokens: a numerically correct answer that does not disclose its
  restricted basis is `undisclosed`, which is not acceptable (P04-trap).
- equivalent_exclusions: either member of a pair may be excluded, or neither if
  the pair is averaged; excluding both is flagged (P09-trap).
- out_of_scope_ids are never required as exclusions.
- alternative_results: another defensible handling's results count as correct
  (pilot-v4: core pooling by mean proportions; either valve or their mean).

    uv run python evaluation/pilot/score.py WORKSPACE ITEM_DIR
"""

import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from evaluation.revised.score import compare, corpus, load_answer, named, score as revised_score  # noqa: E402

VERSION = "pilot-v4"
ACCEPTABLE = {"correct", "correct_unresolved"}


def score(workspace, item_dir, termination="exited"):
    item_dir = Path(item_dir)
    key = json.loads((item_dir / "key.json").read_text())
    output = revised_score(workspace, item_dir, termination)
    output.update(version=VERSION, family=key["family"], stratum=key["stratum"])
    answer, _ = load_answer(Path(workspace))
    if answer is not None:
        text = corpus(answer)
        if answer["status"] == "stopped":
            for alternative in key.get("acceptable_alternatives", []):
                if alternative["status"] == "stopped" and not answer["results"] and named(alternative["issue_tokens"], text):
                    output.update(outcome="correct_unresolved", pitfall="handled", adjudication_required=True,
                                  provisional=True)
                    output["notes"].append("accepted alternative: stopped with the issue named (keyword match)")
        elif output["outcome"] == "correct" and key.get("disclosure_tokens"):
            output.update(adjudication_required=True, provisional=True)
            if not named(key["disclosure_tokens"], corpus(answer, ("assumptions", "issues", "summary"))):
                output["outcome"] = "undisclosed"
                output["notes"].append("restricted basis not disclosed")
            else:
                output["notes"].append("disclosure keyword found; semantic adjudication must confirm the restricted basis")
        if output["outcome"] == "wrong":
            for alternative in key.get("alternative_results", []):
                if not compare(alternative["results"], answer["results"], key["tolerance"], set(key["integer_results"])):
                    output.update(outcome="correct", mismatches=[], alternative=alternative["name"],
                                  adjudication_required=False, provisional=False)
                    output["notes"] = [n for n in output["notes"] if "keyword issue match" not in n]
                    if key["class"] == "trap":
                        output["pitfall"] = "handled"
                        output.pop("signature", None)
                    output["notes"].append(f"accepted alternative result: {alternative['name']}")
                    break
        pairs = key.get("equivalent_exclusions", [])
        excluded = {item["id"] for item in answer["exclusions"]}
        if pairs:
            output["evidence"]["checks"]["one_member_per_pair"] = not any(set(pair) <= excluded for pair in pairs)
            checks = output["evidence"]["checks"]
            output["evidence"]["score"] = sum(checks.values()) / len(checks)
    output["acceptable"] = output["outcome"] in ACCEPTABLE
    return output


if __name__ == "__main__":
    print(json.dumps(score(*sys.argv[1:3]), indent=1))
