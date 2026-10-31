# Independent validation check — 31 October 2026

## Result and scope

Accepted for the declared Llanvirn development cases. The current Python suite
reported **103 passed in 12.70 s** before the PAST capture tests were added.
A separate execution of the R/vegan reference
generator reproduced its committed JSON exactly after excluding `generated_at`:
1,010 numerical values, largest absolute difference zero, no other field changes.

This check was performed by a separate Codex delegate. It used the existing
project renv library, with no restoration, installation or global R changes.
The generator was parsed and evaluated unchanged except that its output path
was redirected into scratch. Existing reference files were not overwritten.

The comparison is between independently authored community-analysis code on
one known development dataset. Both eigensolver paths use LAPACK; agreement
does not establish independence of the numerical linear-algebra foundation,
scientific assumptions, held-out performance or general method validity. This
lane did not operate PAST or generate PAST reference captures.

## Inputs and provenance

Frozen input: `benchmarks/past/legacy-data/llanvirn.dat`, 23 taxa by 10 samples.
Its independently checked SHA-256 matches the R JSON and Python fixture:

`a39a2ec7ef405623efdac5e5cd2b9be7dd38e5ca98c4fe9efa4dab2cda076f37`

The R reader preserves labels using `read.table(..., colClasses = "character",
check.names = FALSE, comment.char = "", quote = "")`, converts the count block
to integers and transposes it into samples by taxa. For this frozen file, the
counts are nonnegative integers, samples are nonempty and labels align exactly
with Python. Integer coercion is not a general-purpose count validator; this
reference reader should remain scoped to the verified fixture.

Runtime: R 4.6.1 (2026-06-24), `aarch64-apple-darwin27.0.0`, macOS 27.0.1;
vegan 2.7-6, permute 0.9-10 and jsonlite 2.0.0. R reports OpenBLAS 0.3.34 and
LAPACK 3.12.1. These package versions match the reference and renv lockfile.

Checked file SHA-256 values:

- Generator: `cdfa68b2e2a73482f8b2c11217e37e18b4b7f702cd05b45a1f4214238fcd7c0e`.
- Committed JSON: `95b815d28f5603487b2bfc4260d1440f97fff5b7e5a0adb20a6d483e2b77a4b9`.
- renv lockfile: `65c9346f954863919a2055897b682aa49197a12221aa6993276b9cd3481f5b07`.

## Numerical comparisons

Definitions agree: Shannon uses natural logarithms; Simpson is `1 - sum(p^2)`;
Jaccard is binary (`binary = TRUE`), whereas vegan's default is quantitative.
The relative-abundance case normalises each sample before Bray-Curtis.
Unweighted `wcmdscale(d, eig = TRUE)` supplies the reference eigensystem.

| Case | Largest absolute Python–vegan difference | Location | Positive / negative non-null axes |
| --- | ---: | --- | --- |
| Relative-abundance Bray-Curtis | 8.881784197001252e-16 | Eigenvalues | 8 / 1 |
| Raw Bray-Curtis | 2.4424906541753444e-15 | Eigenvalues | 8 / 1 |
| Binary Jaccard | 7.216449660063518e-16 | Eigenvalues | 8 / 1 |

The largest diversity difference is 1.1102230246251565e-16; totals and richness
match exactly. Distances differ by at most 1.1102230246251565e-16. All-positive
and first-two-axis Gram matrices agree within 1.3114509478384662e-15. Comparisons
use aligned labels and the non-null spectra, accounting for vegan's omitted
structural null eigenvalue. No eigenaxis sign is treated as evidence of error.
The declared test tolerance remains `1e-10`, scaled by the leading spectral
magnitude where appropriate; the observed error is substantially smaller.

## PAST capture protocol: scoped recommendations

The protocol correctly separates similarities from distances, raw counts from
relative abundance, and current PAST execution from archived examples. Retain
these controls and qualifications during capture:

1. **Similarity versus distance:** use identical and disjoint nonempty sample
   pairs. Similarities must be 1 and 0 respectively; corresponding distances
   must be 0 and 1. For proportional rows, relative Bray-Curtis distance is 0,
   but raw Bray-Curtis distance is the total-imbalance bound. Record the actual
   PAST output labels and diagonal, rather than assuming every module uses the
   same similarity conversion.
2. **PCoA exponent and scaling:** record exponent `c = 2`, eigenvalue scaling
   and all correction/default options. Compare exported eigenvalues before
   coordinates. The manual promises only the first four eigenvalues; a
   four-axis export cannot establish full-spectrum or negative-axis agreement.
3. **Percent denominators:** positive, signed and absolute inertia differ in
   all three cases. Their sums are, respectively: relative Bray-Curtis
   `0.8202957950306277 / 0.8195762484886223 / 0.8210153415726335`; raw Bray-Curtis
   `2.1486855875714435 / 2.147284358224594 / 2.150086816918293`; Jaccard
   `1.3284176098994975 / 1.3188285718397883 / 1.3380066479592068`. Also consider
   the sum over the four displayed axes if the percentages suggest that
   convention. Record the observed denominator convention rather than calling
   a percentage difference a computational failure.
4. **Axis identifiability:** the relative eigengaps at the 4/5 boundary are
   `0.040369540529245046`, `0.046048698781514394` and `0.11675081281207321` in
   that case order. These support comparing the first-four subspace if captured
   with matching scaling. Sign flips are harmless; tied subspaces would require
   geometry comparison rather than axis-by-axis equality.
5. **Export precision:** preserve verbatim numbers. Half a last-place unit
   applies only to rounded output; truncation permits a full unit. Scientific
   notation requires a value-specific significant-digit tolerance. Allow
   machine-level error in addition to the export interval, and set the rule
   before comparing values. Do not apply the internal `1e-10` indiscriminately
   to low-precision PAST exports.
6. **Dielasma missing pairs:** compare separate-locality fits first, recording
   n = 103, 79 and 35. The all-six-column capture is a distinct missing-policy
   experiment; complete-case deletion across columns must not be mistaken for
   disagreement in the regression formula. Preserve both raw and log10 settings.

## Reproduction evidence

Scratch evidence is in `/private/tmp/palaeo-independent-31oct/`:

- `pytest.log`: `.venv/bin/python -m pytest -q` output.
- `regenerate.R`, `regenerate.log`: `Rscript --vanilla regenerate.R`, loading
  the existing `references/r/renv/library/macos/R-4.6/aarch64-apple-darwin27.0.0`
  library and recording `sessionInfo()`.
- `community-vegan-regenerated.json`: isolated regenerated reference.
- `compare.py`, `comparison.json`, `comparison.log`: full recursive comparison
  excluding the timestamp and Python-versus-regenerated-vegan error summaries.

The regenerated reference, recursive comparison summary, R session log and
initial test receipt are now preserved in
[the independent-check archive](../references/independent/2026-10-31/).
The temporary scripts remain scratch work; the committed generator, input,
lockfile and reference JSON provide the reproducible reference workflow.
The subsequent [PAST results](validation-tranche-3-results.md) report the
executed captures and the enlarged test suite.
