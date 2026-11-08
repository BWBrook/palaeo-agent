# Contract: reading a saved Neotoma download (`neotoma_extract`, v1)

Claude (Opus 5.5), 8 November 2026. Specification only; not yet
implemented. The scope follows Codex's sprint-10
[review](sprint-10-review.md) (Board 3031).

## Purpose

Both applications (Lake Selina, Tasmanian surface pollen) needed about 100
lines of intake code. That code turned a saved Neotoma download into a
sample-by-taxon table and sample metadata. Most of it was mechanical and
identical between them:

- walking `data[].site.collectionunit.dataset.samples[].datum[]`;
- filtering by element and ecological group;
- checking units and label uniqueness;
- zero-filling absent taxa;
- flattening site and sample fields.

`neotoma_extract` does that part, deterministically and with provenance.
Every interpretive choice stays with the caller, who declares it in the
study that follows.

## Scope of v1

- **In scope:** the frozen `data/downloads` JSON shape that both
  applications saved, read from a local file whose SHA-256 the caller
  declares.
- **Out of scope:**
  - live retrieval and authentication;
  - other Neotoma endpoints, and the separate chronology responses;
  - non-pollen data models;
  - a general ecological-data workflow.

## Specification

```json
{
  "source": "source/neotoma-tas-surface-download.json",
  "source_sha256": "0205169197c5…58c36",
  "datasets": "all",
  "units": "percent",
  "elements": ["pollen", "pollen/spore", "spore"],
  "ecological_groups": ["TRSH", "UPHE"],
  "absent_taxa": "zero",
  "row_order": "source"
}
```

| Field | Meaning |
| --- | --- |
| `source`, `source_sha256` | Local file and its required hash. A mismatch is refused (`source_hash`). |
| `datasets` | `"all"`, or a list of dataset IDs. An unknown ID is refused (`unknown_dataset`). |
| `units` | `"NISP"` gives the table kind `counts`; `"percent"` gives `abundance`. Any other unit is refused in v1 (`unsupported_units`). |
| `elements` | Exact list of Neotoma `element` values to keep. Required, never defaulted. |
| `ecological_groups` | Exact list of `ecologicalgroup` codes to keep. Required, never defaulted. |
| `row_order` | `"source"` (file order) or `"depth"` (dataset order, then increasing archived depth; refused on a missing or tied depth within a dataset, `depth_order`). Required, because `count_homogeneity` with `pairs: "adjacent"` reads table order. |
| `absent_taxa` | Must be `"zero"`. Neotoma omits zero cells, so this declares that absence in a sample's datum list means zero within the kept groups. There is no silent default. |

**Unit handling.** Units are checked on every kept datum. If any kept
datum, or any datum in a selected dataset with no kept data, has other
units, the extraction is refused (`mixed_units`). It never converts
between units.

**No inferred counts.** NISP values must be exact nonnegative integers
(`invalid_count`). Percent values must be finite and nonnegative
(`invalid_abundance`). Percentages are never turned into counts and are
never rescaled.

## Outputs (an extraction bundle)

| File | Content |
| --- | --- |
| `table.tsv` | Delimited, `samples_by_taxa`. The `sample_id` column holds Neotoma `sampleid` as a string. Taxon columns use the source `variablename` labels, sorted by code point. Each cell is the source value or `0`, written with Python `repr`. |
| `samples.csv` | One row per sample, in table order. Columns: `sample_id`, `datasetid`, `datasetname`, `doi`, `siteid`, `sitename`, `collectionunitid`, `handle`, `collunittype`, `depositionalenvironment`, `depth`, `thickness`, `samplename`, `analysisunitname`, `lon`, `lat`, `site_altitude`, `collectionunit_notes`, `sample_notes`, `dataset_pi`, `shares_coordinates_with`. |
| `ages.csv` | The archived `ages` entries, one row per sample and chronology: `sample_id`, `chronologyid`, `chronologyname`, `agetype`, `age`, `ageolder`, `ageyounger`, `is_default_chronology`. |
| `taxa.csv` | One row per column label: `label`, `taxonid`, `taxongroup`, `ecologicalgroup`, `element`, `elementtype`, `units`, `n_samples_positive`. |
| `extract.json` | The specification, the source hash, table `kind`, and counts of datasets, samples, data and labels seen and kept. Also counts of data dropped by each filter, as `{element, ecologicalgroup} → n`. Environment and implementation hashes, as in run bundles. |
| `manifest.json` | SHA-256 and size for each file. |

**How fields are passed through:**

- **Archived values are not reinterpreted.** `depth` is the archived depth
  field, and `dataset_pi` is the archived PI. Neither is relabelled as a
  stratigraphic surface or as a sample analyst.
- **`shares_coordinates_with`** is only a flag. It lists other site names
  whose archived coordinates are identical.
- **Notes are copied verbatim** and are never parsed.

## Refusals

| Code | Condition |
| --- | --- |
| `source_hash` | The source bytes do not match `source_sha256` |
| `invalid_source` | The JSON is not the `data/downloads` shape: a required key is missing or has the wrong type |
| `unknown_dataset` | A declared dataset ID is absent from the file |
| `duplicate_sample` | The same `sampleid` appears twice |
| `repeated_label` | One sample has two kept data with the same `variablename` |
| `label_collision` | One label maps to more than one `taxonid`, element or ecological group across kept data. The extractor never merges categories; harmonise later with `map_taxa`. |
| `unsupported_units` / `mixed_units` | As above |
| `invalid_count` / `invalid_abundance` | As above |
| `depth_order` | `row_order: "depth"` with a missing or tied depth within a dataset |
| `empty_selection` | No kept datum remains |

A sample whose kept data are all absent stays in the table as an all-zero
row. The analysis's `empty_samples` policy then governs it, and
`extract.json` lists such samples.

## What stays with the caller

| Choice | Where it is declared |
| --- | --- |
| Which samples to analyse (for example "sample 1 of each surface dataset") | study `select`, with a reason |
| Altitude or other overrides read from notes; groups such as bands | the caller's metadata CSV, joined in the study. That code remains declared glue. |
| Excluding or harmonising taxa | study `exclude_taxa` and `map_taxa` |
| Pollen-sum denominator; closure | analysis `transform` |
| Imputation, age models and the choice of chronology | caller, declared in the report |

## Interfaces and inspection

- **Engine.** `neotoma.py` holds the engine and depends on no transport.
  The Python entry point is `pa.neotoma_extract(spec, output_dir)`.
- **CLI and MCP.** A CLI subcommand `neotoma-extract` and one MCP tool
  are thin wrappers over the engine.
- **Inspection.** `inspect_run` on an extraction bundle re-reads the
  source, checks its hash, re-derives every file and compares bytes.
  Reproduction does the same in a new directory.
- **Studies.** A study can use `table.tsv` directly as an input, with the
  study `kind` equal to the extraction `kind`. Binding a study input to an
  extraction bundle, so that the study checks that the kinds match, is a
  possible later layer. It is not part of v1.

## Acceptance

1. **Tasmanian surface pollen.** `analyses/tas-surface/intake.py` is
   reduced to the extractor plus its declared glue (band assignment from
   notes, the study file). The 61 × 92 table must match the current
   `data/percent.tsv` cell for cell, and the study results must stay
   byte-identical.
2. **Lake Selina.** The extractor, with `units: NISP`, `elements:
   ["pollen"]`, groups TRSH and UPHE and `row_order: "depth"`, reproduces
   the archived 66-category count table `data/counts.tsv` cell for cell,
   in the same row order. That table holds exactly these pollen groups;
   the sedge and aquatic exclusions come later, in the study.
3. **Tests:**
   - each refusal code;
   - zero-fill;
   - an all-zero kept row;
   - preservation of labels and IDs;
   - determinism, shown by reproducing a bundle twice;
   - rehashed tampering with `table.tsv` and with `extract.json`.
4. **Documentation.** The primer adds the extractor to the operation
   catalogue, with its non-goals.
