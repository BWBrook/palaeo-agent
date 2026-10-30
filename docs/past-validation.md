# PAST example corpus and numerical validation

## Target and present evidence

Target: account for every publicly available example dataset associated with
PAST 5 within a documented source scope, then compare the supported documented
analyses against actual, versioned PAST outputs. The complete public PAST 5
corpus has not yet been enumerated or acquired. Barry supplied the version 5.4
manual and original 2001 case-study ZIP; the legacy corpus is preserved under
his explicit private-repository authorisation. No PAST numerical reference runs
have been performed by this project.

The official site currently lists Windows PAST 5.4 and a Mac 5.2 download. The
linked manual identifies itself as version 5.4. Record the version actually
running, platform and executable provenance for every reference run. A download
page label or an old screenshot is not an execution record.

The 2001 site contains fourteen case studies. These are a separate legacy
source, not evidence that PAST 5 has exactly fourteen example datasets.
The [legacy inventory](../benchmarks/past/legacy-cases.json) maps all fourteen
captured cases to the seventeen acquired datasets. Original HTML and offline
reading copies, with source provenance, are available from the
[archived index](../benchmarks/past/vignettes/html/doc1.html).

## What a comparison means

Track separate levels of evidence:

1. **Acquired:** exact input bytes and provenance have been recorded.
2. **Parsed:** labels, values, dimensions and missing-value meaning are checked.
3. **Executed:** a declared method/settings combination runs successfully.
4. **Compared:** actual outputs are assessed under predetermined rules.
5. **Validated for the stated case:** the comparison and independent scientific
   checks support a narrowly worded claim, with remaining limitations stated.

One dataset may support several methods and settings. A reproduced table or
figure may contain many outputs. Keep all these counts distinct. Public
datasets are known benchmark material, not held-out evidence; add independent
analytical, synthetic and external fixtures to challenge generalisation.

## Reference capture

For each comparison preserve the original dataset and its checksum, source and
attribution, PAST application version/platform, complete sequence of selections
and preprocessing, resolved settings, output tables and figures, and the
capture date. Prefer exported numerical outputs; screenshots alone may lose
precision and hide settings. Record any manually transcribed reference values
and check them independently.

A manual example is useful evidence but may describe an older implementation.
Label its version and distinguish published values from outputs newly generated
in PAST. If only documentation exists, report that reference execution remains
pending. Do not synthesize plausible PAST results from our backend.

## Numerical acceptance

Define tolerances per output, using its scale, conditioning, export precision
and expected algorithmic differences. Do not impose a universal decimal-place
rule or adjust a threshold after seeing a failure without documenting and
justifying the amendment.

- Deterministic statistics: compare estimates and relevant intermediate values,
  while matching denominators, log bases, bias corrections and missing-data rules.
- Distances: check definitions, abundance/binary treatment and matrix alignment.
- Ordination: compare eigenvalues, reconstructed geometry and appropriately
  aligned scores. Axis signs, rotations in degenerate subspaces and arbitrary
  orientations must not produce false failures. Document scaling conventions.
- Clustering: account for tied distances, valid alternative leaf orderings and
  linkage definitions rather than comparing an image pixel by pixel.
- Permutation and bootstrap outputs: distinguish equality using identical
  supplied random draws, when available, from agreement within justified Monte
  Carlo uncertainty. A shared seed across different RNGs is not shared draws.
- Optimisation: inspect objective values, convergence and repeated starts;
  similar-looking plots are insufficient evidence.

Record a result as matched, explained difference, unresolved discrepancy or
unsupported. An explained difference is not numerical identity. Do not
reproduce a demonstrated scientific bug merely to match PAST.

## Independent checks

Use exact small examples, analytical expectations and meaningful invariants.
Examples include symmetry and the diagonal of distances, sample relabelling
with consistent metadata, and known bounds for a declared diversity definition.
Only assert invariants that the particular method actually satisfies.

Include edge cases: empty samples, absent taxa, noninteger counts, duplicate
identifiers, missingness, rank deficiency and non-Euclidean distances where
relevant. Check permutation exchangeability and distinguish location from
dispersion effects in ecological group comparisons. Cases outside supported
designs must fail explicitly or remain unsupported.

## Data access and distribution

Public download availability does not establish an open redistribution licence.
Record the terms applying to each dataset separately from PAST's software terms.
Barry explicitly requested preserving the uploaded sources and captured pages
in the private development repository. Their original rights remain attached;
public release requires a separate distribution review. See
[THIRD_PARTY.md](../THIRD_PARTY.md).

The scope and current source observations are maintained in [sources.md](sources.md).
