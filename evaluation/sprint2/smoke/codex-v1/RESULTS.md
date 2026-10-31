# Sprint-2 frozen Codex feasibility smoke

Twelve of twelve planned trials completed normally: **12 automatic primary
scores correct**, comprising ten completed numerical cases and two reasoned
stops on the dependent design. There were no timeouts, controller retries,
replacement trials or ceiling-stopped launches. Both keyword-based G2 stop
scores were reviewed against the answers and executed saved scripts; the
automatic scores remain unchanged.

Live source: `1093bb0c4a4d7ef556658418210fae3bcac79881`. Instrument freeze: `b670270`.
The model/effort requested in every command was `gpt-6.1-sol`, medium; observed
CLI version was `codex-cli 0.166.0`. The stream does not independently attest an
internal model build. All 69 frozen file hashes still matched immediately after
the controller finished, before the subsequent source repair.

| Observed measure | Direct | Toolkit |
| --- | ---: | ---: |
| Correct primary scores | 6/6 | 6/6 |
| Completed numerical cases | 5 | 5 |
| Reasoned dependent-design stops | 1 | 1 |
| Counted tokens | 95,613 | 135,226 |
| Mean counted tokens/trial | 15,935.5 | 22,537.7 |
| Mean elapsed seconds/trial | 67.3 | 69.7 |
| Mean frozen evidence-checklist score | 0.792 | 0.958 |

Total counted usage was **230,839** uncached input plus
output tokens, below the 300,000 launch-stop ceiling. Aggregate trial elapsed
time was 822.5 seconds. Full input, cached-input
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
wheel at `1943c30` did not receive these live trials**. Its subsequent
numerical validation is separate, and this smoke does not validate it.

Recompute summaries with `python evaluation/sprint2/smoke/codex-v1/summarize.py`.
Recompute frozen automatic scores with `python evaluation/sprint2/score.py
evaluation/sprint2/smoke/codex-v1`. No model calls are made by either command.
