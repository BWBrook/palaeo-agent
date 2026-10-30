# Vision and scope

## Purpose

Give scientific agents a dependable ecology and palaeontology toolkit whose
operations can be discovered, composed, checked and reproduced. The scientist
supplies questions, interpretation and judgment through their chosen agent.
The toolkit supplies scientific computation and inspectable evidence.

The central product question is: does this make agent-led analysis more
correct, easier to check and easier to reproduce than an agent assembling an
equivalent script directly from general scientific libraries?

Barry explicitly confirmed this as the project's north star on 30 October
2026. A paper should be able to specify versioned Palaeo-Agent API operations
and their inputs rather than maintain a bespoke implementation of common
analyses. The operational aim is reproducibility and verification by
construction: capture the executable specification, data, implementation,
environment and checks. This is not a universal guarantee of numerical identity
across platforms or correctness of a scientific interpretation.

## Direction established in the founding discussion

Barry described the aim as "an ecology and palaeontology analysis toolkit
designed for programmatic scientific work" and specified that "people interact
with it only via their Codex or Claude agents". A native Python implementation
with no R runtime is the current direction. A dedicated human-facing GUI is
outside the scope.

Barry also proposed verification against all public datasets used as PAST 5
examples. This is the target corpus, subject to an explicit inventory of what
is publicly available. Dataset availability, attribution and reference outputs
must be established rather than assumed.

## Value beyond existing libraries

The package earns its place through a consistent scientific contract:

1. Data meaning is explicit: samples, taxa, counts, occurrences, measurements,
   metadata, zero values and missing values are distinguished.
2. Analysis settings are resolved and recorded, including transformations,
   distance definitions, exclusions, estimators and randomisation.
3. Errors and warnings identify actionable scientific or data problems.
4. Results include numerical outputs, diagnostics, figures and provenance.
5. Methods carry documented assumptions, supported designs and references.
6. Saved specifications can rerun without the originating chat or model.

An agent remains responsible for choosing a defensible scientific question and
interpreting evidence. The package can validate declared requirements; it
cannot infer that an observational design justifies a causal claim or that an
unrecorded sampling process satisfies an assumption.

## First useful capability

A complete community-data workflow: ingest a sample-by-taxon count matrix and
sample metadata, validate alignment and data meaning, calculate selected
diversity measures and dissimilarities, produce an ordination and diagnostics,
and save an evidence bundle. Add a group comparison only for a declared design
whose permutation requirements the implementation supports.

The first demonstrator need not implement this entire workflow at once. Start
with one numerical operation that already has a defensible reference, while
carrying it through the complete execution and evidence path.

## Success criteria

- A coding agent discovers and executes a supported method without reading
  implementation source or relying on undocumented settings.
- Invalid inputs produce structured, informative failures; no silent data repair.
- The same specification and frozen inputs reproduce the scientifically relevant
  outputs within predefined, method-appropriate tolerances.
- A second agent can inspect the evidence and detect a deliberately unsuitable
  input or failed diagnostic.
- Comparisons with direct library use demonstrate a concrete benefit in error
  prevention, evidence completeness or reproducibility. Wrapper overhead alone
  is not success.
- Claims about PAST name the tested version, datasets, methods and settings.

## Expansion and exclusions

Grow through scientifically useful modules: community ecology first, then
occurrence/stratigraphic analysis, time series, morphometrics or phylogenetics
as actual use cases justify them. Treat these as candidate directions, not
promised features.

Defer GUI development, hosted services, embedded language models, automatic
hypothesis selection, a universal workflow language, a general plugin market,
GPU support and exhaustive PAST feature parity. Human-readable reports and
publication-quality figures remain core outputs despite the absence of a GUI.

## Authority and release

The founding tranche established a local repository and reviewable design.
Barry subsequently authorised the first implementation, source capture and
push to GitHub main in an initially private repository: "Proceed with your
recommended next tranche. And push to GH main as an initially private repo
(whilst we develop it)." Routine local development, verification
and commits follow Barry's standing reversible-work policy. First public
release, external correspondence and publication remain subject to his review.
No redistribution right for PAST software or third-party examples is inferred
from public availability. Choose the project's software licence before release
after checking the selected dependencies; none is asserted by this scaffold.

Record AI contributions and the actual systems/versions used during development.
Do not infer model versions from product names.
