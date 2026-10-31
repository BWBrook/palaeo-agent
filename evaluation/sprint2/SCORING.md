# Sprint-2 scoring amendment

Version `sprint2-group-score-v1`, prepared before live trials.

Use the original `evaluation/score.py` primary numerical comparison, answer
contract, failure signatures, pitfall categories and evidence checklist in both
arms. Record its SHA-256 in the freeze manifest. The original scorer is imported
with `ITEMS` redirected; it is not edited.

One amendment applies to G2-trap: the sampling description explicitly specifies
dependent subsamples with one site per facies. A correct response must have
`status="stopped"`, `results={}`, and name both site IDs plus the dependence or
subsampling problem in `issues`, `assumptions` or `summary`. A completed
calculation, including one marked assumption-dependent, is wrong even if it
names the problem or its arithmetic matches the independent-row calculation.
The original scorer's generic unresolved logic is therefore tightened by the
wrapper. Keyword-based issue detection still requires recorded adjudication.

G3 adds the requested integer `claim_supported` to the numerical key. The trap
expects 0; the clean qualified claim expects 1. Scientific correctness requires
all requested numerical outputs and this claim assessment to match. This
measures response to a supplied interpretation, not spontaneous interpretation.
No keyword alone establishes a correct completed numerical answer.

All other primary rules are unchanged. Tolerance is `max(1e-4,1e-4*abs(key))`;
declared integer outputs match exactly. Automatic scores are preserved;
adjudication is recorded separately. The twelve trials are feasibility smoke
only, with no efficacy claim, tuning or retries.
