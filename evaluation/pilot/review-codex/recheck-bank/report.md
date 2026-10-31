# Pilot-v2 bank amendment verification

Codex, 1 November 2026. Reviewed `a3ca5706a3cc5b72a26c854366d4c887cfdd9b82`.
This is an unblinded recheck of amendments to the previously sealed independent
review, not a new held-out validation. Neither `build_bank.py` nor the toolkit
was read/imported for these calculations. Existing evidence is unchanged.

## Numerical result

All nine recomputed targets match their current keys exactly in float64:
P01-trap, P04-trap/cal, P08-trap/control/cal and P09-trap/control/cal. The
independent script uses rational Bray–Curtis distances and separate RMA and
Shannon formulas. All applicable stored error signatures also agree.

| Check | Result |
| --- | --- |
| P01 zero-coded core included | Mean BC `0.7446141396204127`, n = 13; corrected signature verified. |
| P08-trap | Mean BC `0.2343287881515876`, n = 9. |
| P08-cal | Mean BC `0.2649284508518656`, n = 7. |
| P08 boundary | Every 1 cm slice is wholly on one side; minimum gap to boundary is 0.5 cm. Keyed out-of-scope IDs exactly equal omitted samples, including the control. |
| P09-trap | Slope `0.7602003259773435`, intercept `-0.9999018522079091`, n = 30. |
| P09 alternatives | Keeping the paired left valve, retaining the right valve, or averaging each pair produces identical values for trap and calibration. Counting both valves reproduces the stored error signatures. |

## Sufficiency amendments

- **P01:** Removing “all cores” makes an observed-assemblage summary defensible.
  Core 3 remains unobserved; the result must describe the counted subset and
  record its exclusion, not estimate the missing core's assemblage. The new
  witness explicitly distinguishes those quantities.
- **P02:** Random sites within zones, separated by at least 2 km, now provide
  the intended sampling-design basis for the permutation test. The wording
  permits a permutation test without requiring 999 distinct allocations.
- **P04:** Exact size-fraction coverage now supports a valid common-fraction
  comparison. Full-community 2017 Shannon is still unidentified, as correctly
  acknowledged by the amended witness and stopped-answer alternative. The
  common-fraction basis must be disclosed.
- **P06:** The revised permutation wording permits exact enumeration of the
  20 three-versus-three allocations. Aliquot pooling and core-level units are
  unchanged.
- **P08:** No boundary-coincident or boundary-straddling sample remains. Depth
  filtering now has a unique answer under the supplied age model.
- **P09:** The task specifies individuals rather than a prescribed valve side.
  The measurement equality makes equivalent ways of representing one
  individual agree. Its correctness scoring and evidence scoring both need to
  recognise those equivalents.
- **P12:** The task explicitly requests descriptive pseudo-F and R² with no
  p-value; the previous inference-design objection is resolved.

## Remaining scoring requirements

**P09 left-ID exclusions conflict with accepted alternatives.** The trap and
calibration keys still require all four left-valve IDs in
`exclusions_expected`. The current scorer's `evidence()` consequently awards
the `expected_exclusions_recorded` check only to dropping left valves. A valid
answer dropping the corresponding right valves or averaging pairs fails that
check. The receipt contains runnable examples: all three score numerically
correct, but the otherwise identical sparse evidence scores are 0.4 for
dropping left valves and 0.2 for the other choices. Those absolute scores are
not representative final-package scores; their difference isolates the
incorrect exclusion requirement. Represent permissible grouping/exclusion
choices or adjudicate the one-individual-per-pair handling; do not require an
arbitrary valve side.

**P04 disclosure needs enforcement beyond the proposed three scorer additions.**
The draft only adds alternatives, out-of-scope IDs and strata to the old
scorer. A schema-valid answer with the keyed common-fraction numbers, no
coverage issue or assumption, and the summary “These are the mean Shannon
indices for both campaigns” currently scores `correct`, with
`issue_named=false` and `adjudication_required=false`. That does not satisfy
the witness's explicit requirement to disclose the restricted basis. Add a
check or adjudication for that qualification. The existing scorer also calls
the valid coverage stop `false_refusal`; this latter behaviour is already
covered by Claude's announced, still-pending alternatives amendment.

No remaining numerical defect was found in the amended keys. These scoring
requirements remain before bank/scorer acceptance. Difficulty remains an
empirical calibration question; these repairs establish answerability, not
that the bank will discriminate analyst performance.

## Reproduction

Run `python3 evaluation/pilot/review-codex/recheck-bank/recheck.py` from the
repository. `receipt.json` records all material hashes, key hashes, script and
scorer hashes, independent calculations, and the exact scorer challenges.
No live model calls ran and no production, bank or old review file was edited.
