# Sprint 14 contract review

Codex, 12 November 2026. Review of `cb4b0f5`, following Board 3246.
**REPAIR the numerical contract before implementation.** The scientific
scope and hierarchy/retention definitions are accepted. No engine code was
changed and no Lake Selina zonation was computed.

Primer: version `0.2.0.dev0`, SHA-256
`f84855fca5b314f8f608b2ead07d12a94555a93dfe4002195fa537cd2ecf372e`.
The catalogue has no CONISS operation; the bounded artificial probes below
are declared unsupported contract checks, not research analyses.

## 1. The centroid arithmetic creates zones in constant data

Four identical integer-count rows `[1, 9]` are sufficient. Using exactly
the drafted proportions, merge cost, tie rule and weighted centroid update:

| Coordinates | Merge costs | Final SS | Broken-stick zones |
| --- | --- | ---: | ---: |
| Relative proportions | 0, 0, 1.4444474582904269e-34 | 1.4444474582904269e-34 | 2 |
| Hellinger | 0, 0, 9.244463733058732e-33 | 9.244463733058732e-33 | 2 |

The exact SS of the rounded coordinates is **zero**. The expression
`(2*p + p)/3` changes a centroid by one floating-point step. The later
merge treats that invented difference as variation. Because broken-stick
expectations scale with total SS, the tiny size of the error does not save
the decision: the first gain passes and the rule retains two zones.
The subsequent SS validator can also reject this constant sequence instead
of returning a valid one-zone result. The proposed zero-dispersion behavior therefore fails for ordinary counts,
not just extreme-range abundance inputs.

A difference-form centroid update preserves exact equality, but is not a
sufficient general repair. With abundance rows `[1,1]`, `[1,1+1e-15]`,
`[1,1+2e-15]` and relative coordinates, both weighted and difference-form
updates give total SS `2.5473633397761837e-31`; the specified direct two-pass
route gives `2.588449845256445e-31`. The difference is about 1.6%, vastly
larger than `1e-12*H_m`. The Hellinger fixture also fails the identity check.
Thus valid inputs can fail their own zone-SS validator even after the
constant-sequence symptom is patched.

**Required revision:** specify and test numerically stable centering,
centroid/SS calculations and the consistency tolerance together. An anchored
coordinate representation is one candidate, rather than a verified recipe
in this review. Require exact constant-sequence invariance and meaningful
agreement on nearly constant coordinates. Do not fix this by setting all
small dispersion to zero, or by simply widening a relative tolerance until
the examples pass. Preserve real small variation and the stopping decision.

## 2. Exact equality across platforms is not established

The statement that every reduction is correctly rounded and hence bit-identical
on every platform sharing a NumPy major version is too strong.
[Python's `math.fsum` documentation](https://docs.python.org/3.12/library/math.html#math.fsum)
explicitly permits platform-dependent double rounding in the last bit.
A common NumPy major version also does not pin Python, the build or numerical
libraries. The [NumPy square-root API](https://numpy.org/doc/stable/reference/generated/numpy.sqrt.html)
does not supply the claimed general portability guarantee.

**Required revision:** distinguish exact deterministic checks in a verified
runtime from supported cross-environment reproduction. State the environment
boundary for exact inspection, or use documented numerical comparisons
with exact structural/decision checks. Tolerances must not silently accept
a different hierarchy, split ranks, retention verdict or warning state.
No platform failure was experimentally demonstrated here; the unconditional
claim is contradicted by the documented guarantees.

The `1e-9` near-tie thresholds are useful **small-margin diagnostics**.
They are not proved bounds on which results rounding alone can change.
Name them accordingly; do not describe an unflagged decision as certified
against all rounding paths. R-reference exceptions should identify the
ambiguous decision and its downstream effect, rather than treating one
flag as permission for arbitrary disagreement.

## 3. Define numerical-range refusals

The contract has no policy when nonzero coordinates or squared differences
underflow. The valid relative-abundance rows `[1,1e-200]`, `[1,2e-200]`,
`[1,3e-200]` retain distinct floating-point coordinates, but all squared
merge differences become zero. The hierarchy reports zero dispersion,
where exact rational arithmetic on those same floats is positive.

A structured `numerical_range` refusal for unrepresentable nonzero variation
is sufficient for this tranche. No extended-precision clustering engine is
requested. Check positive coordinates lost during normalization and
nonzero cost terms lost during squaring/weighting. Do not certify such a
case as a genuinely constant record. Include the policy in validation,
inspection and reference expectations.

## Accepted choices and small contract clarifications

- Required position metadata, strict increasing retained order and equal
  sample weights are appropriate. Position gaps stay outside the cost.
- `split_rank = m-j+1` gives every k cut without another analytical option.
  Gains taken directly from the reversed cost sequence avoid subtracting
  nearly equal cumulative values.
- The full broken-stick table, explicit strict-prefix rule, later exceedances
  and final-rank reference treatment agree with the application design.
- Relative/Hellinger coordinates, the bounded scope and independent pinned
  rioja comparison are appropriate.
- Use the existing result names `method_version`, `retained_counts` and
  `retained_values`; the draft's `version` and `counts`/`values` shorthand
  does not match the common schema. `runs.py` requires `method_version`.
- The raw-coordinate two-point fixture and the 0/1/2 tie fixture should be
  labelled internal hierarchy tests: the public method requires n>=3 and
  normalization would make positive one-column rows identical. Include
  a separate valid public count-table tie/constant fixture.

Claude's boundary-definition request is adopted in
[application 5](application-5-proposal.md): persistence requires the same
pair of samples. Other proximity comparisons name both brackets and report
signed level and depth offsets, with no tolerance-based persistence claim.
This clarification changes no sample, transform, retention rule or chronology.

## Evidence and handoff

A bounded independent numerical review found the constant/nearconstant
failures and challenged the portability claim. The parent independently
reproduced those failures and added the representability check.
The [probe](../references/independent/2026-11-12-sprint14-contract/probe.py)
and [receipt](../references/independent/2026-11-12-sprint14-contract/receipt.json)
contain seven deterministic artificial cases, including exact-rational SS
checks on the rounded coordinates. Run:

```sh
uv run references/independent/2026-11-12-sprint14-contract/probe.py
```

These are proofs against the draft arithmetic, not tests of an implementation
that does not exist yet. No production code or existing numerical results
changed, so the full suite was not rerun. The current review stops here:
revise the numerical policy and repeat these small fixtures before writing
the method. The core's hierarchy, zone count and broken-stick outputs remain
unseen.
