# Application 4 proposal: an `rma` allometry study on fossil measurements

Claude (Opus 5.5), 8 November 2026. Posted to Codex as Board 3058 (thread
147). Barry asked for it to be saved here and acted on after the
clean-up pass (8 November 2026).

## Why `rma` next

`rma` is the one supported method that no real application has used, and
the study layer's `measurements` input kind has never run on real data.
Three pollen applications have exercised community analysis, PERMANOVA,
rarefaction, count homogeneity and the Neotoma reader. The next defects are
more likely to be in the measurement path.

## Shape

- A genuine allometry question on openly licensed fossil morphometric
  measurements. Examples:
  - whether a lineage's length–width scaling departs from isometry
    (log–log RMA slope against 1);
  - whether two declared groups share a slope.
- Use whatever `rma`'s declared scope supports, and name any unsupported
  part of the question as such.

## Data

- One frozen download with a SHA-256 and a licence that allows
  redistribution (Dryad, Zenodo or PBDB measurement tables are all
  acceptable).
- Specimens must be individually identified.

## Process

1. Codex chooses the data and writes a design fixed before any results.
2. Claude reviews the design.
3. Codex runs it; Claude reviews the results and interpretation.
4. Toolkit defects found on the way become the following sprint.

As with the earlier applications, the case study serves the tool: infer or
interpolate small data issues and press on (Barry, 8 November 2026).

## Dataset and design selected — 9 November 2026

Codex selected the openly licensed paired caliper/AutoMorph measurements of
136 fossil *Lottia edmitchelli*. The pre-results
[design](../analyses/fossil-limpets/DESIGN.md), frozen source, intake and
two-fit study specification are ready for Claude's review. Both fits are
descriptive: the current `rma` has no isometry or slope-difference test.
The methods text's 139 individuals versus the archived CSV's 136 is retained
as an unresolved source discrepancy. No new fit has been computed.

## Approved execution — 9 November 2026

Claude approved the design in Board 3117. The completed
[report](../analyses/fossil-limpets/REPORT.md) gives both fixed fits,
their shared-cohort measurement sensitivity and independent verification.
The dated pre-results record above describes the state before launch.
