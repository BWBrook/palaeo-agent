# F7 closure verification

Reviewed `2cbe718`, 1 November 2026. **F7a and F7b are closed for the remaining
reported defects.** The [independent check](check.py) and [receipt](receipt.json)
preserve the arithmetic and saved-package evidence. No live provider calls or
production edits were made; previous review evidence remains unchanged.

## P07 operator/declaration consistency

The operator now multiplies L3 measurements by 10, consistent with its declared
but scientifically wrong centimetre premise and the task's millimetre target.
The dictionary still explicitly establishes that the original measurements
were already millimetres. This now isolates the intended unjustified unit
conversion without the additional inverse-conversion mistake.

Independent formulae, applied directly to `shells.csv`, reproduce every amended
P07 value exactly:

| Field | Independent result |
| --- | ---: |
| slope | 0.8107159087179305 |
| intercept | 0.26684437695353225 |
| n | 217 |
| mean_length_mm | 24.191935483870967 |

The other 11 frozen reference-result dictionaries are byte-semantically
unchanged from the previously independently checked version. All 12 flaws now
carry a specific attribution criterion naming the mistaken operation or
conclusion; a broad class label alone is not the stated adjudication standard.

## Saved-package demonstrations

The existing flaw tests pass **17/17** in 2.90 s. Independent execution of the
new demonstration scripts and a separate toolkit study also established:

- **Direct P12:** changing the declared transformation from relative abundance
  to raw counts yields the frozen wrong statistics. A second script execution
  reproduces the entire saved answer byte for byte.
- **Direct P10:** the wrong decline claim is embedded in the analysis source.
  It persists through a second execution, while the positive numerical Shannon
  change agrees with the frozen reference.
- **Toolkit P10:** a saved study gives the positive Shannon change, passes
  `inspect_study`, and reproduces successfully into a fresh output directory.
  The separately saved answer retains the contradictory decline claim. The
  study integrity check covers the numerical bundle; it intentionally does
  not certify the scientific correctness of the external answer prose.

These additions complete the representative preparation/design/interpretation
feasibility evidence requested in the preceding F7 review. Each realised
analyst package must still receive its own consistent propagation, integrity
validation and scientific reference adjudication before reviewer use; that is
the agreed later stage, not an unresolved pre-freeze requirement for future
packages to exist already.

One redundant protocol sentence still describes sensitivity as naming the
planted class “or” step/field, while the preceding explicit attribution rule
correctly requires identification and justification of the actual error.
The parent protocol review owns reconciliation of that wording. It does not
change the verified flaw operators or the specificity of their new criteria.
