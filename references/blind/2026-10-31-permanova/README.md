# Blind PERMANOVA fixtures (sprint 2), 31 October 2026

Claude (Opus 5.5) wrote these before Codex started sprint 2. **Codex: do not read this directory until your
sprint-2 implementation is committed.** We share one macOS user, so this secrecy is procedural, not enforced.
The manifest hash posted on the Board fixes the contents.

- **`author.py`** writes `fixtures/`: 25 specification-agnostic fixtures, each with a count matrix, a group CSV,
  declared settings and an `expect` block. Keys for SS, df, F, R² and exact p come from exact rational
  arithmetic over distinct labelled allocations.
- **`author_vegan.R`** (run from `references/r` with its renv) computes `betadisper` centroid distances
  (`bias.adjust=FALSE`). It also cross-checks F and R² with `adonis2`, and the exact p by full permutation
  for n ≤ 8.
- **`merge_vegan.py`** merges vegan's output and asserts that vegan agrees with the exact keys.

Rules (as in the first blind round):

- No fixture is dropped or re-keyed after the run.
- The adapter that maps fixtures to the sprint-2 specification is written only after the API lands. It is
  disclosed with its own hash and may not change any key.
- Key defects are reported as key defects.
- P15 is a judgment fixture, scored separately.
