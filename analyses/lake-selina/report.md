# Lake Selina: counting-error-qualified reanalysis of the archived pollen counts

Claude (Opus 5.5), 8 November 2026. This is stage 2 of the
[proposal](../../docs/research-application-proposal.md). It runs the design
frozen in [INTAKE.md](INTAKE.md) at 42c5a1b, before any result existed, and
reviewed by Codex in [STAGE1-REVIEW.md](STAGE1-REVIEW.md). Every number here
is in `results.json`, under the key named in brackets, or in
`cross-check.json`.

Reproduce from the repository root:

```bash
uv run analyses/lake-selina/intake.py
uv run analyses/lake-selina/run_api.py
uv run analyses/lake-selina/analysis.py
Rscript --vanilla analyses/lake-selina/reference.R /path/to/pinned-iNEXT-source
uv run analyses/lake-selina/cross_check.py
```

Toolkit primer 0.2.0.dev0, SHA-256
`cdec09d1ab058224869120b2ac6de406be62df6ed112373dfa1057492971f765`. The package
environment is under `environment`; run bundles are regenerated under `runs/` (gitignored).

## Summary

- **The archived sequence is coherent:**
  - forest with *Lagarostrobos* at the base (395–427 cm);
  - forest with *Nothofagus cunninghamii* and *Phyllocladus* above it
    (300–390 cm);
  - a long herbfield and grassland interval (160–295 cm), dominated by
    Asteraceae, Poaceae and *Dichosciadium*-type Apiaceae;
  - a return of forest from 155 cm upward.
- **41 of the 71 adjacent 5 cm steps** differ by more than counting noise
  after Holm adjustment (`homogeneity.adjacent_lt_005`). Exactly one pair
  is sensitive to Monte Carlo error (`homogeneity.n_monte_carlo_sensitive`).
- **The largest steps** fall at the forest–herb transition at 150–160 cm,
  and at 275–295 cm near the oldest date.
- **The 45–38 ka comparison is modest.** The two endpoint spectra
  (225 cm against 265 cm) differ beyond counting noise (Holm p = 0.0056),
  but the change is smaller than the median adjacent step: proportional
  Bray–Curtis 0.196 against a median of 0.206. No single taxon survives
  the global taxon Holm family.
- **Within that window, there is a short episode at 255–260 cm** with more
  *Nothofagus gunnii*, *Pherosphaera* and *N. cunninghamii*, followed by a
  return to herbfield by 247 cm.
- **None of this identifies a human or megafaunal effect.** It is
  consistent with Turney et al.'s (2008) reading of "no major change"
  around 41 ka, and it adds a taxon-resolved, counting-error check.
- **The archived chronology misplaces the climatic benchmarks.** IPPD-2
  dates the return of forest (165→125 cm) to about 23–17 ka. The
  "MIS 3 → LGM" benchmark therefore compares peak herbfield (190 cm) with a
  spectrum already in forest recovery (145 cm). That is either real or a
  sign that the bulk-silt dates read too old, and this analysis cannot
  decide which.
- **Rarefied richness at 282 grains is lowest in the most herb-dominated
  levels** (165–190 cm, E[S] 15.8–18.4) and in the basal *Lagarostrobos*
  forest (395–427 cm, 17.9–22.9). It is highest in mixed, transitional spectra.
  Coverage at 282 is at least 0.955 at every level, so the equal-count
  comparison is well posed.
- **Independent check:** all 687 API quantities checked against R (`vegan`,
  the pinned iNEXT coverage function, `fisher.test`) agree. The largest
  absolute difference is 3.5 × 10⁻¹³.

## The record by depth (primary)

**Composition** (per-level counts in `data/counts.tsv`; the step effects are
under `adjacent_steps`). Percentages are of the 66-category terrestrial sum.

| Depth (cm) | Character of the spectra | Comment |
| --- | --- | --- |
| 395–427 | *N. cunninghamii* 13–25 %, *Phyllocladus* 17–39 %, *Lagarostrobos* 3–20 %; herbs ≤ 2 % | The authors read this as substage 5e |
| 300–390 | *N. cunninghamii* and *Phyllocladus* stay high; *Lagarostrobos* falls; Asteraceae 3–22 % | Undated; analysed by depth only |
| 295–300 | Forest taxa fall and herbs rise | Steps 290→295 and 295→300 rank 4 and 7 of 71 |
| 160–295 | Asteraceae 12–38 %, Poaceae 5–44 %, Apiaceae up to 36 %; forest taxa near 0 | Lowest rarefied richness at 165–190 cm |
| 255–260 | *N. gunnii* 6–12 %, *Pherosphaera* 12–13 %, *N. cunninghamii* 2–5 % | A short episode within the herb interval |
| 145–160 | Grasses and herbs fall; *N. gunnii* (to 15 %) and *Pherosphaera* (to 10 %) peak; *Phyllocladus* rises | The largest step: 155→160 cm, Bray–Curtis 0.462 |
| 80–140 | *N. cunninghamii* 8–24 %, *Phyllocladus* 2–31 %, Restionaceae 2–11 % | Forest; the top sample (80 cm) has 18 singletons |

**Largest adjacent steps** (`adjacent_steps[*].adjacent_rank_by_braycurtis`).
Taxa listed are those with taxon Holm p < 0.05. The sign is the forward-time
change, younger minus older, as a share of the sum.

| Rank | Step (cm) | Bray–Curtis on proportions | Holm p | Taxa (forward change) |
| --- | --- | --- | --- | --- |
| 1 | 155→160 | 0.462 | 0.00077 | Poaceae −0.25; *N. gunnii* +0.13 |
| 2 | 275→280 | 0.402 | 0.00077 | Asteraceae +0.25 |
| 3 | 315→320 | 0.392 | 0.00077 | Asteraceae −0.16; *Phyllocladus* +0.14 |
| 4 | 290→295 | 0.381 | 0.00077 | Apiaceae +0.15; *N. gunnii* −0.09; *Pherosphaera* +0.09 |
| 5 | 280→285 | 0.370 | 0.00077 | Asteraceae −0.17 |
| 6 | 150→155 | 0.340 | 0.00077 | *Pherosphaera* −0.08; *Phyllocladus* +0.06; *Microcachrys* −0.05 |

How to read these numbers:
- **Floor on p.** 0.00077 is the smallest Holm-adjusted value that
  99,999 tables allow, (B + 1)⁻¹ × 77.
- **Median effect.** The median adjacent effect is 0.206.
- **Monte Carlo sensitivity.** The one sensitive pair is 345→350 cm
  (Holm p = 0.054, Holm envelope spanning 0.05). It is reported as
  unresolved, not as a change or a non-change.

**Rarefied richness at m = 282** (`levels[*].expected_richness_282`,
`conditional_sd_282`, `coverage_282`). Medians of E[S]:

| Interval | Median E[S] | Range |
| --- | --- | --- |
| Upper forest, 80–140 cm | 23.2 | 20.9–33.7 |
| Transition, 145–155 cm | 28.5 | 24.0–28.9 |
| Herb interval, 160–295 cm | 23.1 | 15.8–30.4 |
| Lower forest, 300–427 cm | 26.3 | 17.9–32.0 |

The conditional SDs are 0–1.8. They describe subsampling within the
retained table only, not between-sample or between-core variation. The
richness here is richness of *pollen categories*, which depends on how
finely grains were identified. It is not the richness of plant species.

**Representation sensitivity** (`compare_relative_vs_raw`). Relative and raw
Bray–Curtis agree closely: Pearson r = 0.997, Procrustes m² = 0.0012. Count
totals vary only from 282 to 529, so raw-count distances carry little
total-imbalance artefact here.
- **Ordination.** PCoA axis 1 carries 53 % of the positive inertia. The
  negative eigenvalues are material (negative-to-positive inertia 0.074) and
  are not corrected (`ordination.relative_braycurtis.warnings`).
- **Comparison link.** The comparison reports `baseline_link_verified:
  false`, because the frozen sensitivity spec did not declare `baseline_run`.
  The distances are unaffected.

## Named comparisons (secondary, chronology-dependent)

Endpoints were frozen by sample ID (`named_comparisons`). Each is shown
beside its archived-model IPPD-1 sensitivity pair.

| Comparison | Pair (cm) | IPPD-2 years | Totals | Bray–Curtis on proportions | Holm p | Taxa at Holm p < 0.05 |
| --- | --- | --- | --- | --- | --- | --- |
| 45–38 ka | 225 / 265 | 36,902 / 45,481 | 417 / 420 | 0.196 | 0.0056 | none |
| sensitivity (IPPD-1) | 190 / 270 | 28,830 / 46,552 | 305 / 329 | 0.349 | 0.00077 | 2 |
| MIS 3 → LGM | 145 / 190 | 20,928 / 28,830 | 353 / 305 | 0.727 | 0.00077 | 7 |
| sensitivity (IPPD-1) | 135 / 165 | 19,097 / 23,132 | 340 / 335 | 0.719 | 0.00077 | 7 |
| Late Glacial → Holocene | 100 / 120 | 7,532 / 15,176 | 360 / 344 | 0.289 | 0.00077 | 1 |
| sensitivity (IPPD-1) | 95 / 120 | 5,758 / 15,176 | 389 / 344 | 0.312 | 0.00077 | 1 |

**45–38 ka.**
- **The endpoint contrast is smaller than a typical 5 cm step.** The
  composition at 225 cm and at 265 cm is herbfield in both, and the two
  differ beyond counting noise but by less than half the adjacent steps
  do. No individual taxon passes the global Holm family.
- **The window holds its own structure** (`adjacent_steps_within`):
  - the step 260→265 cm ranks 10th of 71 (0.285), and 247→255 ranks 24th
    (0.243);
  - between them, at 255–260 cm (IPPD-2 43.4–44.4 ka), *N. gunnii*,
    *Pherosphaera* and *N. cunninghamii* expand briefly before herbfield
    returns by 247 cm (41.7 ka).
- **Under IPPD-1's endpoints (190/270 cm)** the contrast is larger. Those
  endpoints span about 18 ka under IPPD-2, so they take in more of the
  herb interval's variation. The comparison depends on which archived age
  model selects the endpoints.
- **Interpretation.** Nothing here distinguishes human arrival, megafaunal
  loss, fire or a stadial–interstadial oscillation. Steps of similar size
  occur elsewhere in the herb interval (ranks 2, 4 and 5 at 275–295 cm).
  The charcoal record is not in this dataset. What the data show is that
  no compositional change at the window's ends exceeds the record's
  background of 5 cm changes, while a brief expansion of subalpine and
  rainforest taxa within the window is resolved beyond counting noise.

**MIS 3 → LGM.**
- The largest named effect. Moving forward in time, from 190 to 145 cm:
  - Poaceae fall by −0.30, *Dichosciadium*-type Apiaceae by −0.21 and
    Asteraceae by −0.15;
  - *Phyllocladus* rises by +0.15, Restionaceae by +0.12, *N. cunninghamii*
    by +0.09 and *Leptospermum* by +0.07.
- This is a shift from herbfield to the start of forest recovery, not a
  deterioration into the glacial maximum. Under the archived ages, forest
  taxa (*Phyllocladus* 20–31 %) are already established at 125–140 cm,
  which IPPD-2 dates to 17–20 ka. The 14,200 ± 230 ¹⁴C yr BP date at 125 cm
  (about 17 ka calibrated) itself sits in forest spectra.
- **Two explanations:** either forest returned to the Lake Selina catchment
  unusually early, or the bulk-sediment dates carry old carbon and read too
  old.
- **Decision deferred.** That choice needs the 1999 article's own dating
  discussion, regional comparison, and possibly the TAS1402 chronology
  through a supported core correlation. The benchmark label "MIS 3 → LGM"
  holds only under the archived ages.

**Late Glacial → Holocene.**
- Both endpoints are in forest spectra, and only Asteraceae changes beyond
  the taxon Holm family (−0.08 forward in time).
- Under the archived ages this "transition" sits within the forest
  interval. If the dates are too old, the deglacial transition lies deeper,
  near 145–160 cm.

## Unsupported parts

| Subtask | Why the toolkit could not do it | What was used instead | How it was checked |
| --- | --- | --- | --- |
| Neotoma JSON extraction, terrestrial filtering, zero-fill | The study layer cannot read Neotoma JSON or delete taxa | `intake.py` | Codex's independent byte-identical regeneration and cell-by-cell match ([STAGE1-REVIEW.md](STAGE1-REVIEW.md)) |
| Endpoint selection from archived ages | No operation selects samples by an age annotation | Frozen bracketing rule in `intake.py` | Codex checked IDs, depths, spans and counts of levels between |
| Age model | Out of scope; the archived ages are annotations | IPPD-2 as given; IPPD-1 only for endpoint sensitivity | Controls tabulated in INTAKE.md |
| Monte Carlo sensitivity envelope | The API reports tail bounds but not a Holm envelope | Holm applied to the lower and upper Clopper–Pearson bounds (`analysis.py`) | The same Holm routine reproduces the API's adjusted p exactly (`homogeneity.holm_recomputed_matches_api`) |
| Ranking, forward-time sign, reading distances out of the matrices | Reporting arithmetic on API output | `analysis.py` | API Bray–Curtis on proportions equals `community` relative Bray–Curtis for every reported pair (to 1e-15) |

`permanova` was not used: levels in a core are not exchangeable units.

## Toolkit problems found

None in the engine:
- every run verified on inspection;
- validation and execution agreed;
- the 77-pair, 99,999-table homogeneity run took 54 s on the MacBook;
- rarefaction at m = 282 for 72 levels took 0.2 s.

Two notes on use:
1. **The comparison link.** `compare_community_runs` marks the link
   unverified unless the sensitivity spec carries `baseline_run`. A frozen
   design that names both specs in advance cannot know the baseline run ID
   until it has run. A future design could run the baseline first, or the
   toolkit could accept a link to a declared baseline spec. This is a
   usability gap, not an error.
2. **The R reference.** `jsonlite` writes a named R list as a JSON object.
   The cross-check handles either shape. This was my scripting slip, not a
   toolkit issue.

## What this does not establish

- **Cause.** One site's pollen cannot separate climate, fire, herbivore
  release and people.
- **Timing.** Ages near 40 ka are interpolated between bulk-silt dates. The
  oldest date (52,110 ± 5,800 ¹⁴C yr BP) is a weak finite control. The
  archived chronology also appears to place the return of forest
  implausibly early, which is unresolved.
- **The counting protocol.** The 1999 article was not obtained. Zero-filling
  absent entries and treating the archived categories as disjoint are
  stated assumptions.
- **Abruptness, replication and plant species richness.** The tests concern
  how counts are allocated under a multinomial counting model. Serial
  dependence in the core does not invalidate that claim, but the tests are
  not ecological replication.

## Next

1. **Obtain Colhoun et al. (1999).** Check the counting protocol, the
   397 cm against 80–427 cm depth question, and the authors' own reading of
   the radiocarbon dates. If the protocol contradicts the intake, the
   affected runs are amended and rerun under a documented deviation.
2. **Test whether the dates read too old** against independent western
   Tasmanian chronologies. This is a source and literature task, not a
   toolkit one.
3. **Codex review** of this report and `results.json`.
