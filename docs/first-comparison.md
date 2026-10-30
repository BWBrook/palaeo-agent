# First comparison: Dielasma reduced-major-axis regression

Specification recorded before comparison with the package implementation,
30 October 2026. Reference calculations were performed independently using
Python's standard-library `statistics` and `math`, directly from the user-supplied
2001 case-study ZIP. They are not outputs from a current PAST executable.

## Question and scope

Can an agent discover, validate and run an explicit reduced-major-axis (RMA)
regression, then independently inspect and reproduce its numerical evidence
without reconstructing undocumented preprocessing from a chat?

Use the Dielasma example because the archived vignette gives procedures and
rounded answers, its input is available in the uploaded ZIP, and the PAST 5.4
manual documents the same descriptive slope definition (printed pp. 167–171).
This is a first complete operation, not the whole community-analysis workflow.

## Frozen inputs and numerical reference

- ZIP: `benchmarks/past/casefiles.ZIP`, SHA-256
  `34de24563eadb4f895cdd86487b3795c07864ca6e618f5b3edcd3004975804e0`.
- Member: `dielasma.dat`, SHA-256
  `1e471093a057df4d81c944d9f41d2dff4649b205a653c9402083b4a1768249bd`.
- Manual: `docs/past5manual.pdf`, SHA-256
  `499659a327366817350727c31fac2d2828ab55ab45bee4f1b990d98f3de5d1a9`.
- Data have 103 labelled rows and three pairs of locality-specific columns.
  The `.` cells pad the smaller samples; they are not zeros or absences.

For each locality use X1 as x, X2 as y. Request both raw and base-10 log-log
fits, explicitly omitting rows missing either selected value. L1 retains 103,
L2 79 and L3 35 pairs. Record every excluded row ID and reason.

For the retained coordinates, compute sample standard deviations and Pearson's
correlation, then slope `sign(r) * sd(y) / sd(x)` and intercept
`mean(y) - slope * mean(x)`. No intercept constraint, bootstrap, confidence
interval, standard error or hypothesis test is part of this first method.

| Locality | Raw slope | Raw intercept | Log10 slope | Log10 intercept |
| --- | ---: | ---: | ---: | ---: |
| L1 | 0.8427557846904125 | -0.0542366545777284 | 1.0183654435676799 | -0.0978173521167678 |
| L2 | 0.8191670400279810 | 0.2621471236354740 | 0.9817911055076792 | -0.0545622332299502 |
| L3 | 0.9054241567685909 | -0.8029899113932712 | 1.1071123900450557 | -0.1927026641925906 |

The archive's published slopes 0.84, 0.82 and 0.91 correspond to the raw fits.
They do not validate the log-log slopes. The vignette initially asks for
log-log analysis and subsequently considers raw coordinates; preserve both
procedures without inheriting its historical inferential interpretations.

Use `rtol=1e-12, atol=1e-12` for these coefficients against the independently
computed numerical reference. Agreement with the two-decimal published values
has only rounding-level precision (approximately 0.005 absolute tolerance).
These tolerances are specific to this small, well-conditioned example.

## Required challenges and evidence

- Check exact positive/negative linear controls and a base-10 power-law control.
- Challenge duplicate IDs, unknown columns/options, nonnumeric/nonfinite values,
  constant variables, zero covariance and nonpositive log inputs.
- Missing values fail by default; pairwise omission is an explicit alternative.
- Two valid pairs suffice for descriptive coefficients; inference is not offered.
- Verify row permutation invariance and reciprocal slopes after swapping axes.
- Save original bytes, resolved request, retained pairs, exclusions, results,
  diagnostic figures, environment information and checksums.
- Reproduce in a fresh process using only the run bundle and recorded software
  environment. Detect tampering before interpreting a bundle as verified.

Compare this with a direct numerical script, using the same scientific inputs
and formula. The expected advantage is explicit handling of missing data and
complete, inspectable evidence; do not claim that correct direct scripts cannot
do the same, or that the package proves the scientific interpretation.

## References

- [Case 1](https://palaeo-electronica.org/2001_1/past/pastprog/study1.html).
- [Suggested answers](https://palaeo-electronica.org/2001_1/past/pastprog/study1tips.html).
- Hammer, PAST 5.4 reference manual, uploaded PDF, printed pp. 167–171.
