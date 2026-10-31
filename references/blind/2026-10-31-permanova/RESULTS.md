# Blind PERMANOVA fixtures: commitment and result

Claude (Opus 5.5) wrote these 25 fixtures before Codex started sprint 2. Claude posted the SHA-256 of
[`MANIFEST.sha256`](MANIFEST.sha256) on the Board (palaeo-agent thread 102, message 2671):
`621c3edcbb7791746ea649202a0f82553e6a61c6a0965d039da2f9e49e784950`. The 56 files it lists still match.
[`README.md`](README.md) is the original, unchanged note written at commitment.

Codex reports that neither it nor its delegates opened the directory before the run (Board 2687, 2690). Secrecy
relied on that commitment, because both agents share one macOS user. Once published, these fixtures are
development and regression material, not held-out evaluation items.

**Adapter.** [`adapter.py`](adapter.py) maps the fixtures onto the sprint-2 API. Claude wrote it after the API
landed and before any fixture ran, and posted its SHA-256 on the Board (message 2693):
`d07df424cc313d03b4c778bbce3e8153392c772e2f2b91d7401432305b4d027b`. It translates fields only, and its
translation choices are disclosed in its docstring. No key, fixture or adapter line changed after the run.

**Key sources.**
- SS, df, F, R² and exact p use exact rational arithmetic over distinct labelled allocations.
- vegan 2.7.6 `adonis2` agrees on F and R² for all 18 result fixtures, and on the full-permutation p for every
  fixture with n ≤ 8.
- Dispersion keys are vegan `betadisper(type = "centroid", bias.adjust = FALSE)` distances.

## Result at 15723ad

[`results-15723ad.json`](results-15723ad.json) holds the per-fixture records: **24 of 24 objective fixtures
correct, plus the judgment fixture correct.** There were no false refusals and no failures. The run covered
these families:

- **Statistics.** Exact SS, df, F and R² (relative 1e-9), and the space size.
- **Exact p and the exact/Monte Carlo boundary.**
  - Exact p equals its rational key (1e-12), including the all-ties case P05 (F = 1, p = 1) and the
    label-swap maximum P06 (p = 2/70).
  - The boundary behaves as specified: M = 924 at the default B is exact; M = 1260 and M = 1716 at the default
    B are Monte Carlo; M = 1260 and M = 1716 at B = 9999 are exact.
- **Monte Carlo records.** Each has denominator B + 1, a p on the k/(B+1) grid with k ≥ 1, and identical
  indices and p when rerun with the same seed.
- **Stochastic check, reported separately.** Monte Carlo p = 0.001 against exact 0.00079 (P02b), and 0.002
  against exact 0.00058 (P08), both within four standard errors plus one grid step.
- **Metamorphic invariance.** Statistics and p are unchanged under row order, group renaming, and ×1000 counts
  under relative abundance.
- **Dispersion.** Centroid distances and group means agree with vegan to relative 1e-9, including the
  non-Euclidean P23 and the different-spread P24.
- **Refusals**, each with the intended code:
  - `undefined_observed_statistic`: zero within-group variation;
  - `insufficient_groups`;
  - `small_groups`;
  - `missing_group_label`;
  - `metadata_alignment`: ID mismatch;
  - specification validation: dependent design;
  - `empty_samples`.
- **Judgment fixture P15.** An allocation of identical profiles gives a permuted SS_W of 0 with SS_B > 0. The
  implementation counts it as a +∞ exceedance, matching the key: p = 13/15 over 90 allocations. Silently
  dropping the allocation would give 72/84.

[`tests/test_blind_permanova.py`](../../../tests/test_blind_permanova.py) checks the manifest and the adapter
hash, reruns every fixture through the agent-facing path in CI, and requires the same outcomes.
