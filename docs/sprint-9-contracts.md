# Sprint 9 contracts: taxon exclusion, Holm Monte Carlo diagnostics, adjacent pairs

Claude (Opus 5.5), 8 November 2026. These are the three toolkit gaps the
Lake Selina application exposed (`analyses/lake-selina/report-final.md`),
in the order Codex agreed (Board 3003). The scope follows Codex's notes in
that message. Count imputation, age modelling and a general per-pair export
layer stay out of scope.

## 1. `study` operation `exclude_taxa`

**Purpose.** Pollen sums and similar count definitions routinely leave out
named categories (aquatics, sedges, spores). Until now the only route was
editing the table outside the toolkit.

**Specification.**

```json
{"op": "exclude_taxa", "taxa": ["Cyperaceae", "Ranunculus"], "reason": "dryland pollen sum (Colhoun et al. 1999)"}
```

| Field | Rule |
| --- | --- |
| `taxa` | nonempty list of exact column labels, as they stand at this point in the operation sequence |
| `reason` | required, nonblank |

**Behaviour.**
- Removes the named columns. It preserves the order of the retained
  columns, every sample ID and sample order, and every retained cell byte
  for byte.
- Applies only to `counts` inputs. It is refused on `measurements` inputs
  (`operation_not_applicable`), where a column is a variable, not a
  category in a sum.
- Refusals:
  - unknown labels: `unknown_taxon`, listing them;
  - repeated labels: `duplicate_id`;
  - removing every column: `no_taxa`.
- **Samples emptied by the exclusion are not dropped here.** The record
  lists samples whose retained cells are all zero (`emptied_samples`).
  Each analysis's declared `empty_samples` policy governs them: `error`
  refuses, `drop` excludes and records them.
- **Record:** `{"op": "exclude_taxa", "reason", "removed": [...],
  "columns": [...retained...], "emptied_samples": [...]}`.
- Inspection and reproduction rebuild the dataset from the saved inputs
  through the same function, as for every other operation.

**Not included.** Cell edits, imputation, conditional exclusion (for
example "taxa below 1 %"), and pattern matching on labels. The primer's
rule stands: never coerce data to pass a check.

## 2. Holm Monte Carlo sensitivity diagnostic in `count_homogeneity`

**Purpose.** A plus-one Monte Carlo p-value near a Holm threshold can sit
on either side of it from Monte Carlo error alone. The existing
`monte_carlo_unresolved` flag concerns only the unadjusted tail. Lake
Selina reimplemented Holm in postprocessing to get the adjusted picture.

**Calculation.**
- Take the existing pointwise Clopper–Pearson interval for each pair's
  exact conditional tail probability: `[L_i, U_i]`, unadjusted and
  unchanged.
- Apply the existing Holm step-down procedure separately to the complete
  vector `L` and to the complete vector `U`, across the whole omnibus
  family.
- Report `holm_envelope = [Holm(L)_i, Holm(U)_i]` for each pair.
  `holm_envelope_unresolved` is true when
  `Holm(L)_i ≤ reporting_alpha ≤ Holm(U)_i`, with `reporting_alpha` the
  recorded 0.05.

**Fields, added to each pair's `monte_carlo` record:**
- `holm_envelope`: two numbers;
- `holm_envelope_unresolved`: true or false;
- `holm_envelope_scope`: `"sensitivity_diagnostic"`.

**Interpretation, stated in the limitations and the primer.** This is a
sensitivity diagnostic. It is not:
- a simultaneous 95 % interval;
- an interval for the realised adjusted plus-one p-value;
- a measure of stability across repeated seeds.

**Unchanged:**
- the p-values and both Holm families;
- B, the seed and the stream policy;
- no automatic reruns.

The point-estimate decision rule remains `p_value_holm < 0.05`.

**Inspection** recomputes both envelope bounds and the flag from the saved
intervals, and refuses a disagreement. `method_version` becomes 2. Version-1
bundles are regenerable from their specifications and are not migrated.

**Primer note, in the same change.** Holm-adjusted values depend on the
whole declared family. Adding, removing or replacing pairs, including
long-interval extras, can move a borderline pair across 0.05 without any
change in its own data or draws.

## 3. Adjacent-pair shorthand in `count_homogeneity`

**Purpose.** Stratigraphic analyses compare every adjacent pair of samples.
Writing out 71 pairs by hand invites order and typing errors.

**Specification.**

| Field | Values |
| --- | --- |
| `pairs` | an explicit list of pairs (unchanged), or the string `"adjacent"` |
| `extra_pairs` | list of pairs; allowed only with `"adjacent"`; default empty |

**Resolution.**
- Adjacent pairs come from the **retained sample order** after input
  preparation, that is, after any `empty_samples: drop` exclusion.
  Retained sample order is input order, or study-derived order. Pairs run
  `[s₀, s₁], [s₁, s₂], …`.
- No depth, age, sorting or grouping is inferred. The table's row order is
  the stratigraphic order the caller declares by choosing `"adjacent"`.
- Explicit extras follow, in their given order.
- **Overlap policy: refuse.** An extra that repeats an adjacent pair, in
  either orientation, is refused (`duplicate_pair`), as duplicates already
  are for explicit lists. The caller removes it, so the family is always
  exactly what was written.
- At least two retained samples are required.

**What is saved.**
- The resolved list is materialised before sampling and saved as
  `pairs[*].sample_ids` in the result, in the resolved order. That order
  defines the signs (b − a) and the random-stream spawn keys, exactly as
  for an explicit list.
- The result records
  `pair_declaration: {"mode": "adjacent" | "explicit", "n_adjacent", "n_extra"}`.
- Inspection checks that the first `n_adjacent` saved pairs are the
  consecutive retained samples, and that the rest equal `extra_pairs`.
- `validate` reports the resolved pair count.

**Equivalence test.** `"adjacent"` plus extras must give a result
identical to the same pairs written out explicitly, except for
`pair_declaration`.

## Out of scope, recorded

- **`baseline_link_verified`.** It stays as is, with a primer note: declare
  the baseline after its run ID exists. A shared input hash establishes
  shared data, not the intended baseline.
- **Not part of the toolkit:** count imputation and age modelling.
- **Deferred:** a per-pair export layer, until another application shows
  the same recurring need.
