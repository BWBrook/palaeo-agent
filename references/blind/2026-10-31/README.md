# Blind validation fixtures, 31 October 2026

Claude (Opus 5.5, interactive session) wrote 61 fixtures with analytical,
metamorphic or adversarial keys. It used the documented specifications and
public API of Palaeo-Agent at e04b592, and only after the fixtures were
complete did it run them against that revision. Codex, the implementer, did
not see them before the run. They are blind to the implementer, not to the
code: Claude had reviewed the tranche 2 source in its earlier adversarial
review. Now that they are published, they count as development material under
[evaluation.md](../../../docs/evaluation.md) and must not be reused as
held-out evaluation items.

## Commitment and rules

Before any run, Claude posted the SHA-256 of [`MANIFEST.sha256`](MANIFEST.sha256)
on the Board (palaeo-agent thread 101, message 2650):
`1e249c530fe5b7e5ef18ed3049cbe9c2919c7e29dda5cba47ec703e122731807`. The
manifest lists per-file hashes for `author.py`, `runner.py`,
`fixtures/fixtures.json` and the 45 data files, and every file here still
matches it. Three rules were fixed in advance:

- no fixture is dropped or re-keyed after the run;
- harness fixes are disclosed with a new hash (none were needed);
- key defects are reported as key defects.

[`author.py`](author.py) generates the fixtures without importing
palaeo_agent. Keys come from the definitions in exact rational arithmetic:
Bray-Curtis, binary Jaccard, Simpson, the double-centred matrix and its trace
and sum of squares. Floating point is used for Shannon, the RMA formulas and,
through `numpy.linalg.eigvalsh`, the eigenvalues of exactly computed
double-centred matrices.

[`runner.py`](runner.py) drives each fixture through the agent-facing path:
`palaeo_agent.runs.run`, and for sensitivity fixtures `compare_community_runs`
as well. `AnalysisError` and pydantic `ValidationError` count as structured
refusals; any other exception counts as a failure. A numerical check passes
when `|actual − key| ≤ tol · max(1, |key|)`.

## Result at e04b592

| Family | Fixtures | Correct | Not correct |
| --- | ---: | ---: | --- |
| RMA | 26 | 26 | — |
| RMA, judgment | 1 | 0 | R09b |
| Community | 29 | 28 | C04 |
| Sensitivity | 5 | 5 | — |

There were no false refusals and no unstructured failures. Every refusal
carried a code matching the fixture's intended reason, for example
`nonpositive_log`, `zero_covariance`, `invalid_encoding`, `metadata_alignment`
and `comparison_baseline`. Per-fixture records, including actual values,
keys and refusal codes, are in [`results/e04b592.json`](results/e04b592.json).

The checks covered:

- Analytic RMA keys, including a negative slope, an exact log10 power law, a
  1e8 offset, a 1e-12 scale and two pairs, held within 1e-12 relative (1e-9
  for the 1e8 offset).
- The symmetry and affine-equivariance relations held.
- Exact rational Bray-Curtis and Jaccard distances, plug-in diversity, the
  spectrum's trace and sum of squares, a non-Euclidean case with a
  substantial negative eigenvalue (−0.174), the two-sample and equilateral
  spectra, and every metamorphic invariance. These comprise the all-zero
  taxon, double-zero Jaccard, relative-BC scale, sample permutation,
  orientation transpose, ×1e9 counts and metadata order.
- The sensitivity statistics matched independently computed Pearson,
  average-rank Spearman, symmetric Procrustes m² and total-imbalance keys.

## Findings

**C04: arbitrary axis from a tied eigenspace (defect).** Three samples with
disjoint supports have all pairwise distances equal to 1. They form an
equilateral configuration with eigenvalues ½, ½ and 0. With `dimensions=1`,
the analysis returns one coordinate axis, `[0, −0.5, 0.5]`, and no warning.
Any rotation within that two-dimensional eigenspace is equally valid, so the
axis carries no information beyond the solver's arbitrary choice.

The 1e-8 relative-eigengap identifiability rule exists in the sensitivity
comparison, but the community analysis does not apply it at the declared
cutoff. The generic limitation that orientations within tied eigenspaces are
arbitrary does not tell an agent that this particular result is affected.
Assemblages with no shared taxa are common in palaeontological data, so this
is not a curiosity. The key expected a refusal. A structured warning with
null coordinates would also prevent the misreading.

**R09b: near-zero correlation diagnostic (judgment).** With n = 8 and
r = −0.043, the fit returns a slope of −0.332 with no warning. The
`near_zero_correlation` warning fires only when |r| < 1e-8, although its
message, "Slope direction is unstable near zero correlation", describes the
statistical situation. The magnitude of the RMA slope is s_y/s_x whatever r
is, so with weak association the line describes a dispersion ratio rather
than a relationship. Whether to warn at a declared |r| threshold, or to defer
to the planned slope-test method, is a design decision. The fixture is scored
separately for that reason.

## Reproduce

```sh
uv run python -I references/blind/2026-10-31/author.py      # regenerates fixtures/ in place
uv run python -I references/blind/2026-10-31/runner.py references/blind/2026-10-31/fixtures /tmp/blind.json
```

Run `author.py` only to audit the keys: it rewrites `fixtures/`, and the
manifest check should still pass afterwards.
