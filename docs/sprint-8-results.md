# Sprint 8: instructed use of the toolkit (I1, I2)

Claude (Opus 5.5), 6 November 2026. Analyst sessions: Claude Sonnet 5.5
(`claude-sonnet-5-5`) through Claude Code 2.1.311, full launcher route,
subscription login. Checks fixed before launch in
[`evaluation/sprint8/checks.md`](../evaluation/sprint8/checks.md) (e750964).
Records: [`evaluation/authentic/run-records/sprint8-instructed-20261106/`](../evaluation/authentic/run-records/sprint8-instructed-20261106/).
Codex's independent review ([`sprint-8-review.md`](sprint-8-review.md),
8c9fc3c) corrected parts of this summary; the corrections are applied below
and carried into the [joint report](sprints-7-8-report.md).

**What this can show.** Two sessions, one model, one client: descriptive
evidence that delivery and instructed compliance *can* work on the two
paths. Not a compliance rate, not evidence about voluntary adoption (A1 and
A2 remain the only evidence there), and the difference between the cases
cannot identify a causal effect of the bootstrap.

## Freeze and qualification

- Pre-freeze study change: `row_filter_removes_pairs` warning, to Codex's
  contract (106dc69). Runtime `~/palaeo-eval/sprint8-runtime-20261106` built
  from 106dc69; wheel SHA-256 `0935d468…`; the installed primer equals the
  committed bytes (`47cab284…d3`, 9,675 bytes).
- Offline client probe (no model calls): all three full-route cases pass;
  bare toolkit/MCP still suppresses server instructions, as in sprint 7, and
  is not the launch route. Worker probes pass; native suite 688 passed.
  [`evaluation/sprint8/qualification.json`](../evaluation/sprint8/qualification.json).

## Outcomes

| Check | I1 Coed Duon, MCP-native | I2 Dielasma, Python bootstrap |
| --- | --- | --- |
| User told about the primer | no | yes (print the whole `primer()` object) |
| 1. Primer available in runtime | yes | yes |
| 2. Full body in a tool result before the first analytical call | yes: its first tool call was `primer`, unprompted | yes: call 0 |
| 2. Body visible in the transcript | yes | yes |
| Listed operations called (final package) | `community` (3 representations + `compare`), `rarefaction`, `count_homogeneity` | `validate`, `rma` (log10 and raw, three localities) |
| Final-package compliance | yes: API calls plus glue; no supported quantity computed by its own code | partial: computes and reports the unique-pairs L2 slope itself; recomputes n, means and SDs that its raw-scale `rma` results already hold |
| Whole-session compliance | partial: horizon totals computed with pandas during exploration | partial: as for the final package |
| Unsupported-parts table | present | present, four rows with reasons and checks |
| Primer SHA-256 in report | truncated (`47cab284…913d3`) | full |
| Unsuitable design forced | no; declined PERMANOVA on horizons, with the primer's reason | no; descriptive `rma` never presented as inference; intervals labelled as its own bootstrap |
| Warnings reported with a conclusion | negative eigenvalues | L2 `repeated_block` and `repeated_pairs`, L3 repeats; unique-pair sensitivity |
| Package replays (fresh confined worker) | byte-identical | byte-identical |
| Counted tokens (session + retrospective) | 57,602 + 41,026 | 47,435 + 33,883 |

Mechanical scores: [`score-I1.json`](../evaluation/authentic/run-records/sprint8-instructed-20261106/score-I1.json),
[`score-I2.json`](../evaluation/authentic/run-records/sprint8-instructed-20261106/score-I2.json).
The old A2 record, run as a negative control, scores no delivery.

## Judged findings

**I1.** The final `analysis.py` is API calls plus glue. During exploration,
though, it summed horizon totals with pandas (worker audit line 9), which
`community` and `rarefaction` provide: a small whole-session breach (found
by Codex). The science is careful. 5→6 is the robust major change in every
representation. 6→7 is large but resolved only by Basil's absence at 26
specimens, and confounded with the unconformity. Zero-count limits are used
correctly (Basil ≤ 0.109 at horizon 7, compatible with ~10 % but not 47 %).
Raw-count Bray–Curtis is identified as count-total confounded. It also
stated what the data cannot establish (effort, time, cause, absence).
Codex's review corrects four report statements: the omnibus is a Monte
Carlo conditional test, not an exact one; non-rejection at 1–2 and 2–3 does
not make horizons 1–3 indistinguishable (1–3 was untested) or equivalent;
Sower is not the most abundant taxon at horizon 6, rather than uniquely
non-dominant; conditional expected richness at size 13 is not a population
richness claim. Two further lapses:
- it reported a truncated SHA-256;
- after passing the `compare` result dict where `inspect_comparison` wanted
  a path, it read `report.json` from the comparison bundle directly. The
  read is glue, but it skips the integrity check that `inspect_comparison`
  performs.

**I2.** Slopes come from `rma`; `validate` precedes each run. Every
inferential step is declared as unsupported, with a reason: bootstrap
slope intervals and differences, Kruskal–Wallis, Mann–Whitney and KS. Its
own RMA, needed inside the bootstrap, is cross-checked against the API to
1e-9, as primer §7 allows. It reports the L2 block. It computed only the archived results and a
unique-pairs slope (0.977, matching the corrected analysis's 0.97653); my
earlier statement that it kept all three scenarios' consequences visible
was wrong. Codex reran its six-test Mann–Whitney/Holm family under the
removal scenarios: L1–L2 length goes from Holm p 0.023 (archived) to 0.055
(block removed) and 0.072 (unique pairs), so "all three pairs differ" is not
robust to the unresolved record problem; the L3 contrasts stay below 0.05.
Further lapses, all in the saved `analysis.py` and so in the final package
(rechecked after Barry's review of the joint report, 7 November):
- **A rule breach in the reported results.** The unique-pairs *point* slope
  (0.977, quoted in the report) was computed with its own `rma()` on a
  deduplicated array. `study` exclusion plus `rma` is the supported route,
  and the step is not in its unsupported-parts table. The bootstrap interval
  around it is legitimately bespoke.
- **Recomputed supported quantities.** Its `summary` block recomputes n, mean
  and SD of length, and mean width, from its own parse of the file. The
  raw-scale `rma` results it had just saved hold the same quantities
  (`n`, `mean_x`, `sd_x`, `mean_y`), and the two agree exactly. The report
  quotes n in its slope table but does not separately cite the duplicated
  summary fields; `results.json` carries both sets. It also counts the
  eight L2 duplicate pairs from the raw array, where the `repeated_pairs`
  groups the API returned give the same count.
- **Undeclared bespoke descriptives.** Medians, ranges, skewness, length
  histograms, the share of shells under 10, width/length ratios and an OLS
  slope have no toolkit operation, so code is allowed for them, but they are
  missing from the unsupported-parts table, which the rule requires.
- **One scientific error.** It said raw-scale slopes (0.82–0.91) are below 1
  "only because the intercept is not zero". In fact the raw slope of width on
  length is near the width/length ratio (≈ 0.84) because widths are smaller
  than lengths, and that is what isometry predicts. Its conclusion, that
  only the log–log slope bears on allometry, is still right.

Neither session used `study`, so the new row-filter warning was not
exercised live.

## Deviations, stated plainly

1. **Budget overrun.**
   - The agreed ceiling was 120,000 counted tokens with launch-stop. The
     harness counts the retrospectives. I2 launched at 98,628 spent, and
     the total was **179,946**: sessions 105,037 and retrospectives 74,909.
   - The overrun is 50 %. I did not project the retrospectives' cost, which
     resume the whole session context. They cost 41k and 34k, about 70 % of
     the sessions themselves.
   - For future runs: either budget the retrospective as part of each
     session's projected cost at launch, or drop it when the record already
     answers its question.
2. **The scorer was fixed after the sessions.** It missed I2's delivery.
   The agent printed the primer JSON and then a directory listing in the
   same call, so stdout was not a single JSON document, and in the
   transcript that JSON sits inside the worker's JSON-wrapped stdout. The
   fix parses each line and nested JSON strings. The check's definition is
   unchanged, and the A2 negative control still scores no delivery. The
   diff is in the commit that adds these results.

## Recommendation on primer and delivery

- **Both paths delivered the full primer before analysis.** I1's final
  package used the API for every supported quantity; its session did not
  (exploratory totals). I2's final package called `validate` and `rma` but
  also computed and reported one supported quantity itself (the
  deduplicated slope) and recomputed others (n, means, SDs). An earlier
  version of this summary said both final packages used the API for every
  supported subtask; that was wrong for I2. The mechanical check
  (`supported_subtasks_through_api`) tests only that each listed operation
  occurs in the package, so it cannot detect recomputation; only a reading
  of the code can.
  This is consistent with Barry's hypothesis that A1 and A2 ignored the API
  because they were not firmly told to use it. Two sessions cannot establish
  it.
- **Keep the explicit bootstrap line as the documented baseline.** It names
  the primer and costs the user one sentence. MCP-native delivery also
  worked here with only "use the toolkit": the server instructions led the
  agent to call `primer` first. One session cannot show that it does so
  reliably, and it fails under `--bare`.
- **Primer clarifications, applied after the runs** (primer SHA-256 now
  `cdec09d1…`; the sessions used `47cab284…`):
  - add `inspect_comparison(dir)["report"]` to the §4 table;
  - ask for the full, untruncated SHA-256 in §9;
  - in §3, name `study` exclusion plus `rma` as the route for a
    deduplicated sensitivity;
  - in §1, list exploratory checks of supported quantities among the
    non-grounds for bypassing the API.

## Next

Reviewed by Codex; see the [joint report](sprints-7-8-report.md).
