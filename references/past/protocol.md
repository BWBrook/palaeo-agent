# PAST 5.4 reference capture protocol

Status: proposed by Claude (Opus 5.5), accepted and executed by Codex on
31 October 2026 (Board #2642–2643). See the
[results](../../docs/validation-tranche-3-results.md) and
[capture manifests](captures/). E0 remains deferred: native Copy exports
were sufficient. C1–C4 were executed, including all ten PCoA eigenvalues;
coordinate comparison remains limited to the first four axes.

## Purpose

Obtain actual PAST outputs for the cases where Palaeo-Agent implements a
definition PAST also documents. This moves those named cases from "executed"
to "compared" in [past-validation.md](../../docs/past-validation.md). PAST is
one comparator alongside the [vegan references](../r/README.md) and analytical
controls. Investigate any disagreement. Never tune settings to obtain
agreement.

## Comparator

- `/Applications/Past5.app`, bundle `no.uio.Past5`, App Store build 1.0.12.
  Its About dialog reads "Past 5.4" (Codex, Board #2609, 30 October 2026).
- At the start of each capture session, record the About text with a
  screenshot, plus the macOS version and hardware model.
- PAST accepts a data file and a startup script on the command line, and
  scripts can call `clickmenu` and write files. Whether a module's numerical
  results can reach a file without GUI interaction is untested; experiment
  E0 decides it.

## Rules for every capture

1. Record the committed input's path and SHA-256 before opening it. Change data
   inside PAST only through declared operations such as transpose or column
   selection, and record each as a step.
2. Record every option visible in the module window, including defaults left
   unchanged. A settings screenshot is secondary evidence and never replaces
   the written record.
3. Take numbers from PAST's own copy or export function, saved verbatim to a
   text file. Transcribe from the screen only when no export exists. Mark
   transcribed values as such and have a second read confirm them.
4. Record the precision PAST exports. Comparison tolerances come from that
   precision, not from our internal `1e-10`. Use a token-specific half-unit
   rounding bound at the module's observed significant digits, restoring
   omitted trailing zeroes, plus an explicit floating-point allowance.
5. Record stochastic outputs, such as bootstrap intervals and permutation
   p-values, with their replicate counts. Do not compare them for equality.
6. Use one directory per case: `captures/<case-id>/capture.json`, verbatim
   exports in `raw/`, and screenshots in `screenshots/`.
7. Keep failed or ambiguous captures. If a capture is repeated, keep both and
   say why.
8. After changing a numerical option, press Recompute where available before
   copying output. The diversity module can display results from the previous
   setting alongside the newly changed checkbox.

`capture.json` records: `case_id`, `captured_at`, `by` (agent and
model as reported), `past_about`, `macos`, `input` (path, SHA-256),
`data_steps`, `module_path`, `settings`, `outputs` (paths, hashes, exported
digits and acquisition kind), and `notes`. Verbatim text remains in the
referenced raw files.

## E0: scripting feasibility

Launch PAST with a data file and a script that calls `clickmenu` for one module
and writes a file. Record whether any module result reaches the file without
GUI interaction. The outcome changes only how captures are made.

## Cases, in run order

**C1. Llanvirn similarity matrices** (Similarity and distance indices).
Transpose `llanvirn.dat` (SHA-256 `a39a2ec7…f37`) so that samples are rows,
and check the row labels are 1 to 10. Export the full Bray-Curtis and Jaccard
matrices. The manual (printed pp. 160–162) defines both as similarities:
Bray-Curtis as 1 − Σ|xᵢ − yᵢ| / Σ(xᵢ + yᵢ), and Jaccard as M / (M + N) on
presence and absence. Expect PAST similarity = 1 − our distance. C1 settles
the distance definitions independently of any ordination convention.

**C2. Llanvirn diversity** (Diversity → Diversity indices). Use the file as
supplied, because PAST expects taxa in rows and samples in columns (printed
p. 194). Leave "Unbiased" off. Compare, per sample: taxa S with `richness`,
individuals n with `total`, Simpson 1 − D with `simpson`, and Shannon H (natural
log) with `shannon`.

**C3. Dielasma RMA** (Model → Linear, bivariate; method RMA). For each of L1,
L2 and L3 (SHA-256 `1e471093…249bd`), select X1 and X2, untransformed and
with PAST's base-10 log option for both axes. Compare slope a, intercept b
and Pearson r with our `rma` results and with
[first-comparison.md](../../docs/first-comparison.md). Also record the
standard errors of a and b. These are the PAST reference for the planned
slope-test method and are not compared now. Then select all six columns
together and record whether missing values are handled per pair (103, 79 and
35 pairs) or by complete-case deletion across the selection (35 pairs for
every locality). This is evaluation trap D1 as PAST handles it.

**C4. Llanvirn PCoA** (Multivariate → Ordination → Principal coordinates).
Transpose as in C1. Run Bray-Curtis and Jaccard with transformation exponent
c = 2 and eigenvalue scaling on, recording every other option. For the
relative-abundance case, record the transform menu step used. Rescaling rows
to percentages instead of proportions leaves Bray-Curtis unchanged. Export the
eigenvalues, percentages and coordinates for every axis PAST reports. The
manual does not state how a similarity becomes a distance before eigenanalysis.
Determine this from C1 and the exported eigenvalues, and report it as an
explained difference if it is not d = 1 − s. Check what PAST's percentages are
relative to; ours are fractions of positive inertia.

## Comparison and reporting

- Declare tolerances from export precision before comparing: at most half a
  unit in the last exported decimal place, or the relative equivalent for
  significant digits.
- Compare coordinates only for axes whose relative eigengap identifies them.
  The vegan reference gives gaps of 0.274, 0.039 and 0.051 at k = 2 for
  relative Bray-Curtis, raw Bray-Curtis and Jaccard. Compute gaps before
  comparing axes 3 and 4. Allow a sign flip per axis.
- Classify each output as matched, explained difference, unresolved
  discrepancy or unsupported, as in past-validation.md. Report the number of
  cases, the number of outputs compared and the number matched.
- Claims name PAST 5.4 (macOS App Store build 1.0.12), the capture date, and
  the cases and settings captured. Nothing more.
