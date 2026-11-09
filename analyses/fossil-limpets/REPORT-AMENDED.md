# Paired measurement definitions shift limpet scaling estimates

The same 136 fossil *Lottia edmitchelli* give a lower width–length scaling
exponent with AutoMorph than with calipers. The paired difference
**AutoMorph minus caliper is −0.147**, with a **95% specimen-bootstrap
percentile interval of −0.239 to −0.049**. That interval excludes zero under
the declared resampling assumptions, and the toolkit's Monte Carlo check
resolves the exclusion. Neither individual magnitude test establishes a
departure from isometry.

This is a measurement-definition comparison within one archived fossil
sample. It does not identify the more accurate method, an individual growth
trajectory or a population-wide allometric exponent. Caliper width/length
and outline minor/major axes need not measure identical geometry.

## Fixed amendment and prior knowledge

[Amendment 1](AMENDMENT-1.md) and its [study](study-amended.json) were
committed at **73596b8** before the paired bootstrap ran. The amendment adds
uncertainty to the original descriptive fits; it keeps all 136 ObjectIDs,
the four measurements, source order and log10 transform. The raw CSV now
reads directly through the toolkit's declared ID/data columns. Its derived
PAST table is byte-identical to the original input table.

The point estimates and reviewer-only single-fit intervals were already
known. Generating the sprint's R references also revealed the magnitude
p-values before this freeze. The paired interval, SE and bootstrap behavior
were unseen. This is a prospectively fixed amendment after descriptive
analysis, not an entirely blind study. The [original report](REPORT.md),
original numerical exports and original design remain unchanged.

## Individual fits

| Measurement definition | n | Log-scale r | Exponent | 95% magnitude interval | p for magnitude 1 |
| --- | ---: | ---: | ---: | ---: | ---: |
| Caliper width / length | 136 | 0.864698 | 1.080737 | 0.991960–1.177460 | 0.075522 |
| AutoMorph minor / major axis | 136 | 0.822180 | 0.933878 | 0.847458–1.029111 | 0.166151 |

All entries come from `fits.<analysis_id>` in
[results-amended.json](results-amended.json). The intervals and magnitude
tests target sigma_y/sigma_x on the log10 scale. Both intervals include 1;
neither test rejects magnitude 1 at 0.05. Failure to reject does not
establish isometry. Separate correlation tests establish positive direction
(p = 6.73 × 10⁻⁴² and 1.35 × 10⁻³⁴). These are marginal inferences, with
no combined 95% confidence claim across direction, magnitude and methods.

Exact single-fit inference assumes independent pairs from a nonsingular
bivariate normal distribution on the analysed scale. That model has not
been established for this fossil lot. The [original scatter/residual
figure](figures/scaling.png) remains applicable: the fits and saved pairs
are unchanged to every stored digit. Both fits and the paired comparison
retain 136 specimens, with no exclusions and no returned warnings.

Caliper lengths span **5.40–25.20 mm**, and AutoMorph major axes
**3.93–23.09 mm** (`x_raw_range`). Width/minor-axis spans are
**3.80–20.50 mm** and **3.26–16.18 mm** (`y_raw_range`). The source describes
139 shells whereas the archived CSV contains 136; that discrepancy remains
unresolved. Caliper values occupy a 0.1 mm grid; AutoMorph values are archived
to 0.01 mm, although the source describes typical AutoMorph resolution of
0.001 mm. Recorded precision does not establish accuracy or instrument error.
Source identity, attribution and licensing remain in [source/source.json](source/source.json).

## Paired uncertainty and simulation error

The two slopes use the same specimens. Resampling those matched rows keeps
the dependence between measurement definitions. The fixed run used **9,999
resamples**, **PCG64 seed 9112026**, and a 95% percentile interval.

| API quantity | Value |
| --- | ---: |
| Observed AutoMorph − caliper slope | −0.146859 |
| Bootstrap standard error | 0.047986 |
| Percentile interval | −0.239478 to −0.049118 |
| 99% Monte Carlo band for lower endpoint | −0.242976 to −0.236744 |
| 99% Monte Carlo band for upper endpoint | −0.051922 to −0.045377 |
| Zero-inclusion resolution | `zero_excluded` |
| Replicates changing slope sign, caliper / AutoMorph | 0 / 0 |

Fields are `paired_summary.difference` and `paired_summary.bootstrap` in
[results-amended.json](results-amended.json). Each endpoint band is
pointwise, not a joint 99% band. They quantify simulation error, not sampling
coverage. Both remain below zero; there was no post-result change in seed,
resample count, confidence level or estimator. No degenerate draw was dropped
or redrawn, and no slope-sign warning occurred.

The percentile interval is a first-order approximation assuming independent,
exchangeable specimens. Absence of sign flips supports numerical regularity
in these draws; it does not establish interval coverage or sampling
independence. The two individual intervals can both contain 1 while a paired
interval for their difference excludes zero: the latter retains the
within-specimen dependence and answers a different question. No paired
p-value was requested or calculated.

## Verification and API coverage

- The study and all three child bundles pass toolkit inspection. A copied
  study reproduces all three complete native result files **byte for byte**
  in a fresh worker, with original application paths blocked and no attempted
  reads from them. See [reproduction-check-amended.json](reproduction-check-amended.json).
- Independent base R checks **30,021 quantities**: magnitude intervals and
  p-values, all 9,999 paired slopes/differences, SE, percentile endpoints,
  binomial endpoint ranks/bands and sign-change counts. Maximum absolute
  difference is **1.89 × 10⁻¹⁵**. NumPy indices were supplied solely to match
  PCG64 draws; R refitted the raw measurements independently. See
  [r-check-amended.json](r-check-amended.json). This verifies arithmetic,
  rather than coverage or scientific assumptions.
- The implementation review repaired six defects and passed **834 tests,
  11 skipped**, including live MCP and fresh-server reproduction. See
  [the review](../../docs/sprint-13-implementation-review.md).

| Work | Route / check |
| --- | --- |
| ID/data-column selection, both RMA fits, inference and ranges | Toolkit study and inspected run fields |
| Paired bootstrap and Monte Carlo resolution | Toolkit `rma_paired`; inspect and fresh reproduction |
| Source/hash assertions and compact export | Formatting/provenance code; inspected child-result hashes retained |
| Independent arithmetic reference | Declared external base-R check; every replicate checked |
| Sampling assumptions, fossil interpretation, measurement meaning | Scientific interpretation; no supporting toolkit operation |

The ID-column, raw-range and paired-uncertainty gaps that motivated sprint
13 are closed for this application. Independent-group common-slope inference
and a measurement-error model remain unsupported. They are not required to
answer this paired question. The exact API replicate CSV is preserved as
[bootstrap-amended.csv](bootstrap-amended.csv); full regenerable bundles are
kept locally, with IDs, hashes and environments in
[provenance-amended.json](provenance-amended.json).

Run from the repository root:

```sh
uv run analyses/fossil-limpets/analysis-amended.py --output analyses/fossil-limpets/runs-amended-new
uv run analyses/fossil-limpets/reproduce-amended.py
uv run analyses/fossil-limpets/reference-amended.py
```

The output directory must be fresh. Reproduction checks the copied native
study; the R reference uses the committed numerical exports and source.
The original frozen descriptive workflow is retained as historical evidence.
