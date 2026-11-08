# Contract: reading a saved Neotoma download (`neotoma_extract`, v1)

Claude (Opus 5.5), 8 November 2026. Amended after Codex's sprint-11
[review](sprint-11-review.md) (Board 3037). The amendment makes dataset
selection explicit, defines acceptance by identity, specifies metadata
encoding, pins the age mapping, and makes bundles portable with explicit
inspection. Implemented in `src/palaeo_agent/neotoma.py`.

## Purpose

Both applications (Lake Selina and Tasmanian surface pollen) needed about
100 lines of intake code each. That code turned a saved Neotoma download
into a sample-by-taxon table and sample metadata. Most of it was mechanical
and the same in both. It:

- walked `data[].site.collectionunit.dataset.samples[].datum[]`;
- filtered by element and ecological group;
- checked units and label uniqueness;
- zero-filled absent taxa;
- flattened the site and sample fields.

`neotoma_extract` does that part deterministically, with provenance.
Every interpretive choice stays with the caller and is declared in the
study that follows. This is an intake adapter, not an analysis.

## Scope of v1

- **In scope:** the frozen `data/downloads` JSON shape that both
  applications saved, read from a local file with a declared SHA-256.
- **Out of scope:**
  - live retrieval and authentication;
  - other endpoints, including the separate chronology responses;
  - non-pollen data models;
  - a general ecological-data workflow.

## Specification

The surface example, as it runs. These are the 25 percentage datasets; the
download's two NISP datasets, 74305 and 74913, are left out:

```json
{
  "source": "source/neotoma-tas-surface-download.json",
  "source_sha256": "0205169197c51e03da06e914d157136c965cd7bffb13f103817888ff2fb58c36",
  "datasets": [74429, 75430, 74914, 74643, 74779, 74795, 74778, 74764, 74160, 74142, 74304, 74699, 74569,
               74618, 74701, 74780, 73988, 74777, 74303, 74141, 75423, 74644, 74798, 74766, 75421],
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
| `datasets` | `"all"` or a list of unique dataset IDs. An unknown ID is refused (`unknown_dataset`). Units **validate** the selection and never filter it: `"all"` with `units: "percent"` on the surface download is refused (`mixed_units`), because two datasets are NISP. |
| `units` | `"NISP"` gives the table kind `counts`; `"percent"` gives `abundance`. Every kept datum must carry exactly these units (`mixed_units`). |
| `elements`, `ecological_groups` | Exact lists of Neotoma `element` and `ecologicalgroup` values to keep. Both are required; neither is ever defaulted. |
| `absent_taxa` | Must be `"zero"`. Neotoma omits zero cells, so this declares that absence from a sample's kept data means zero. There is no silent default. |
| `row_order` | `"source"`: file order of datasets and samples. `"depth"`: datasets in file order, then samples by increasing archived depth; a missing or tied depth within a dataset is refused (`depth_order`). It matters because `pairs: "adjacent"` reads table order. Reordering selected samples is done with study `select`. |

**No inferred counts.** NISP values must be integers from 0 to 2⁵³ − 1
(`invalid_count`). Percent values must be finite, nonnegative and
representable in float64 (`invalid_abundance`). The source is parsed with
each number's JSON text kept, so a positive value that would underflow to
zero (for example `1e-400`), or overflow, is refused rather than silently
changed. Units are never converted, values never rescaled,
and percentages never turned into counts.

## Source structure

These keys are **required**. A missing key, or a value of the wrong type,
is refused as `invalid_source`:

| Level | Required keys |
| --- | --- |
| top | `data` (list) |
| record | `site` (object) |
| site | `siteid`, `sitename`, `collectionunit` (object) |
| collection unit | `collectionunitid`, `dataset` (object) |
| dataset | `datasetid`, `samples` (list) |
| sample | `sampleid`, `datum` (list), `ages` (list, may be empty) |
| datum | `variablename` (non-blank string), `value`, `units`, `element`, `ecologicalgroup` (strings), `taxonid` (integer) |

Every other field is nullable metadata, copied when present. The taxon
identity fields `elementtype` and `taxongroup` must be strings or null.

## Outputs

Each extraction writes a self-contained bundle:
`<output_root>/<uuid>/`.

| File | Content |
| --- | --- |
| `source.json` | The exact source bytes |
| `spec.json` | The specification, with `source` resolved to `source.json` |
| `table.tsv` | Delimited, `samples_by_taxa`, written with CSV quoting (tab delimiter). `sample_id` is Neotoma `sampleid` written as a string. Taxon columns use the source `variablename` labels, sorted by code point; the header must read back unchanged through the toolkit's delimited reader. Each cell is the source value written with Python `repr`, or `0` when absent. |
| `samples.csv` | One row per table row, in table order (columns below) |
| `ages.csv` | One row per archived `ages` entry (mapping below) |
| `taxa.csv` | `label`, `taxonid`, `taxongroup`, `ecologicalgroup`, `element`, `elementtype`, `units`, `n_samples_positive` |
| `extract.json` | The derived record. Specification, source hash, table `kind`, counts seen and kept, dropped-datum tallies by `(element, ecologicalgroup, units)`, `all_zero_samples`. It holds no environment data. |
| `environment.json` | The same environment record as run bundles |
| `uv.lock` | Present exactly when `environment.json` records an available checkout lockfile, as in run bundles. It is not part of the derived-file comparison. |
| `manifest.json` | Schema 1, kind `neotoma_extraction`; SHA-256 and bytes for every other file |

### `samples.csv` encoding

- **Columns:** `sample_id`, `datasetid`, `datasetname`, `doi`, `siteid`,
  `sitename`, `collectionunitid`, `handle`, `collunittype`,
  `depositionalenvironment`, `depth`, `thickness`, `samplename`,
  `analysisunitname`, `geometry_type`, `lon`, `lat`, `site_altitude`,
  `collectionunit_notes`, `sample_notes`, `dataset_pi`,
  `shares_coordinates_with`.
- **Values:**
  - `null` → blank field.
  - Strings are copied verbatim.
  - Numbers use Python `repr`.
  - Lists and objects use canonical JSON: sorted keys, `(",", ":")`
    separators and UTF-8. This covers `doi`, which is a list, and
    `dataset_pi`, a list of objects.
- **Geography:** `site.geography` is itself a JSON-encoded string. It is
  parsed, and its `type` is written to `geometry_type`.
  - For a `Point`, `lon` and `lat` are its first two coordinates.
  - For any other type, such as Lake Selina's `Polygon`, they are blank.
    No centroid is inferred, and the full geometry stays in `source.json`.
- **`shares_coordinates_with`** flags, among the selected datasets, other
  site names whose `Point` coordinates are identical. They are sorted and
  joined with `; `.
- **Archived fields keep their archived meaning.**
  - `depth` is the archived depth field and is not read as a surface.
  - `dataset_pi` is the archived PI and is not treated as the sample's
    analyst.
  - Notes are copied verbatim and never parsed.

### Age mapping

- For each table row, in table order, and each entry of that sample's
  `ages` list, in source order, write one row: `sample_id`,
  `chronologyid`, `chronologyname`, `agetype`, `age`, `ageolder`,
  `ageyounger`, `is_default_chronology`.
- The rows are keyed by `(str(sampleid), chronologyid)`. A repeated key is
  refused (`duplicate_age`).
- Values use the `samples.csv` encoding, so null bounds are blank.
- `is_default_chronology` is `true` when the entry's `chronologyid` equals
  `site.collectionunit.defaultchronology`, and `false` otherwise.
- No chronology is chosen, and no separate endpoint is read.
- Expected: 61 rows for the 25 surface datasets, and 144 for Lake Selina
  (72 IPPD-2, the default, and 72 IPPD-1).

## Refusals

| Code | Condition |
| --- | --- |
| `source_hash` | Source bytes do not match `source_sha256` |
| `invalid_source` | Not JSON, or a required key is missing or has the wrong type |
| `unknown_dataset` / `duplicate_dataset` | A declared ID is absent; a dataset ID appears twice in the file |
| `duplicate_sample` | A `sampleid` repeats |
| `repeated_label` | One sample has two kept data with the same `variablename` |
| `label_collision` | One label maps to more than one combination of (`taxonid`, `element`, `elementtype`, `ecologicalgroup`, `taxongroup`). The extractor never merges; harmonise later with `map_taxa`. |
| `mixed_units` | A kept datum has other units than declared |
| `invalid_count` / `invalid_abundance` | Value refusals, as above |
| `depth_order` | `row_order: "depth"` with a missing, non-finite or tied depth within a dataset |
| `unsupported_label` | A label contains a control character (tab, newline, carriage return), or does not read back unchanged through the delimited table reader |
| `duplicate_age` | A repeated `(sampleid, chronologyid)` key |
| `empty_selection` | No kept datum remains |

A sample whose kept data are all absent stays in the table as an all-zero
row. Each analysis's `empty_samples` policy then governs it, and
`extract.json` lists it.

## What stays with the caller

| Choice | Where it is declared |
| --- | --- |
| Which samples to analyse, and their order | study `select`, with a reason |
| Altitude or other overrides from notes; groups such as bands | the caller's metadata CSV, joined in the study. This code stays declared glue. |
| Excluding or harmonising taxa | study `exclude_taxa` and `map_taxa` |
| Pollen-sum denominator; closure | analysis `transform` |
| Imputation, age models, choice of chronology | caller, declared in the report |

## Interfaces and inspection

- **Python:** `pa.neotoma_extract(spec, output_root)`,
  `pa.inspect_neotoma(bundle)` and `pa.reproduce_neotoma(bundle,
  output_root)`.
- **CLI:** `neotoma-extract`, `neotoma-inspect` and `neotoma-reproduce`.
- **MCP:** the tools `neotoma_extract`, `neotoma_inspect` and
  `neotoma_reproduce`.
- **Separate from the method results.** The extractor is not added to the
  scientific method-result union or to `inspect_run`.
- **Inspection:**
  - refuses a symbolic-link or malformed manifest (it must be an object
    with integer `schema_version` 1);
  - verifies the file set and every hash, and that `uv.lock` is present
    exactly when the environment declares it;
  - checks that `spec.json` points to `source.json` and that the snapshot
    matches `source_sha256`;
  - re-derives `table.tsv`, `samples.csv`, `ages.csv`, `taxa.csv` and
    `extract.json` from the snapshot and compares them byte for byte;
  - validates `environment.json`.

  It needs nothing outside the bundle, so it still works after the
  original source has moved.
- **Reproduction** re-extracts from the snapshot into a new bundle, then
  compares the derived files byte for byte. It reports
  `environment_identical` separately, because a different revision changes
  only the environment record.

## Acceptance

1. **Tasmanian surface pollen.** `analyses/tas-surface/intake.py` uses the
   extractor with the specification above.
   - Its table must equal the previous 61 × 92 `data/percent.tsv`, value
     for value, keyed by sample ID and label. That earlier file sorted
     sample IDs globally; the new one keeps source order.
   - The study keeps its explicit `select` order.
   - The numerical results must stay identical. They are compared apart
     from the primer hash, which changes with the primer.
2. **Lake Selina.** With `units: "NISP"`, `elements: ["pollen"]`, groups
   TRSH and UPHE and `row_order: "depth"`, the extractor reproduces the
   72 × 66 `data/counts.tsv` value for value and in the same row order.
   That table already matches both source and depth order. The age rows
   match the archived IPPD-2 and IPPD-1 ages in `data/levels.csv`.
3. **Tests:**
   - every refusal code;
   - zero-fill and an all-zero kept row;
   - preserved labels, IDs and metadata encoding (nulls, lists, Point
     against Polygon);
   - the age mapping;
   - determinism;
   - inspection after the original source is moved;
   - rehashed tampering:
     - a source snapshot changed against its declared hash;
     - changed filters in `spec.json` against the derived outputs;
     - edits to `table.tsv` and `extract.json`.
4. **Primer:** it adds the extractor to the operation catalogue, with its
   non-goals.
