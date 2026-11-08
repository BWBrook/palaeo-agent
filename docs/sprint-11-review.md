# Sprint 11 and saved-Neotoma reader review

Codex (`gpt-6.1-sol`), 8 November 2026. Reviewed `7dfe07b`.
Production code, tests and application outputs are unchanged by this review.

**Accept sprint 11. All three sprint-10 range findings are closed.**
The saved-download reader has the right scope; clarify the five items below
in its contract before implementation, then proceed.

## Implementation checks

- Full suite: **736 passed, 11 skipped**. The process cleanup test ran
  with process-list access; optional native confinement tests were not enabled.
- The original file/native overflow and positive-to-zero examples now
  return structured refusals. Common-factor rescaling gives the expected
  Bray–Curtis distance of 1/21. Ordinary count arithmetic is unchanged.
- Independent R `binom.test`/`qbeta`: **30 fields across 10 cases agree**
  at absolute tolerance 1e-12; maximum difference **1.11e-16**. Cases
  include b = 0, b = B, small B, both sides of 0.05, 49/999 and 687/9999.
  This checks interval arithmetic and the threshold flag, not ecological
  uncertainty or the validity of exchangeability.
- Existing Monte Carlo and exact fixtures retain F, R², p, distances,
  permutation indices, statistics and all other pre-existing permutation
  fields exactly. Exact enumeration reports null interval and flag.
- Four rehashed semantic attacks on bounds, flag, status and an inserted
  interval in an exact run fail inspection. Live MCP discovery, schema and
  results expose method version 2 and all five new fields correctly.
- A fresh surface-pollen study and the existing report summariser reproduce
  the committed `results.json` byte for byte. Its study inspects as verified.
  The composition interval is 0.0638249554–0.0738417566; the binary interval
  is 0.1560215160–0.1706078490. Neither contains 0.05. The expected unequal
  group-size and negative-eigenvalue warnings remain.

The interval estimates the conditional randomisation tail probability from
the independent draws. Keeping the plus-one p, schedule and decision rule
unchanged is correct. The new diagnostic does not assess sampling-design
uncertainty.

Keeping the original reference-pinned PERMANOVA contract intact is acceptable.
It is a historical reference specification. The README's current method link
should also point to the version-2 amendment in `sprint-11.md`, so users do
not have to discover the amendment through the review history. No reference
hash or original reference values need changing.

## Reader contract: clarify, then build

1. **Use an executable dataset-selection example.** The illustrated
   `datasets: "all", units: "percent"` must refuse the surface download:
   datasets **74305 and 74913 are NISP**. Show the explicit 25 percentage
   dataset IDs for that example. Units validate the selection; they do not
   silently filter datasets.
2. **Define acceptance by identity where order differs.** The existing
   61 × 92 surface table globally sorts sample IDs. Neither proposed order
   reproduces that order. Require equal values keyed by sample ID and
   source label, then preserve the existing study's explicit `select` order.
   No additional ordering mode is needed. Selina's 72 × 66 table already
   matches both source and depth order. After adding the extractor to the
   primer, compare numerical application results separately from the
   necessarily changed primer hash in its aggregate `results.json`.
3. **Specify metadata nulls, lists and geometry.** Both real sources have
   null thickness, sample names and sample notes; Selina also has null
   analysis-unit names. Notes and age bounds can be null. Define blank CSV
   fields for nulls and canonical JSON for list/object fields: `doi` is a
   list and `dataset_pi` a list of dictionaries. Geography is itself a
   JSON-encoded string. Surface geometries are Points; Selina is a Polygon.
   Copy Point coordinates to lon/lat, leave non-Point coordinates blank and
   retain the original geometry in the source snapshot. Do not infer a
   centroid. Distinguish required structural keys from nullable metadata.
4. **Pin the age-field mapping.** Read each sample's `ages`, keyed by
   `(str(sampleid), chronologyid)`. Copy the stated fields directly;
   `is_default_chronology` compares that entry's chronology ID with
   `site.collectionunit.defaultchronology`. Expected output is **61 age
   rows** for the selected surface records and **144** for Selina: 72
   default IPPD-2 and 72 alternative IPPD-1. This needs no separate
   chronology endpoint and makes no chronology choice.
5. **Make extraction bundles portable and inspection explicit.** Include
   the exact source bytes in the bundle and manifest, and resolve the saved
   specification to that internal snapshot. Inspection and reproduction
   must still work after the original external source has moved. The
   current scientific `inspect_run` schema does not accept this extraction
   layout. Prefer explicit `inspect_neotoma` / `reproduce_neotoma` entry
   points with thin CLI/MCP wrappers; do not force an extractor into the
   scientific-method result union. Recompute deterministic derived files
   from the snapshot, while treating environment and implementation
   provenance separately when reproducing under another revision. Test
   rehashed changes to the source snapshot against the declared source hash,
   and changed filters against their derived outputs, as well as table edits.

No label collisions were found under the contract's rules in either
selected example, including taxon group and element type. Preserve the
agreed boundaries: saved downloads only; sample selection, altitude
overrides, harmonisation, closure, imputation and chronology choices stay
with the caller. This is an intake adapter, not a new analysis programme.

## Review provenance

Primer version **0.2.0.dev0**, SHA-256
`343bda600f9c0dd136d310efb1bcbb369c74d699b954beaeafa7f74214d3bc46`,
read in full. The relevant catalogue and schemas were checked. Supported
analysis and replay used the API. Unsupported review work was source-shape
inspection, adversarial fixture generation, field comparison and the
independent R reference; these do not replace reported API quantities.

The bounded independent checks confirmed the interval arithmetic and live
transport; the saved-source audit changed the reader acceptance requirements
above. The parent reviewed their receipts and ran the full suite and fresh
application replay. Numerical agreement and replay do not establish the
scientific validity of the worked example.

The compact arithmetic evidence is in
[`references/independent/2026-11-08-sprint11/`](../references/independent/2026-11-08-sprint11/checks.json).
Regenerate its interval comparison from the repository root:

```bash
uv run references/independent/2026-11-08-sprint11/generate.py
Rscript --vanilla references/independent/2026-11-08-sprint11/reference.R \
  references/independent/2026-11-08-sprint11
```
