# Study bundles

A study composes declared data preparation with the supported analyses and
saves everything as one bundle that another agent can inspect and rerun.
It is the sprint-4 product layer in the [revised plan](sprints-3-4-proposal.md).
Nothing is inferred: a label merge, an exclusion, a missing-value decision or a
sampling assumption happens only if the study declares it.

```json
{
  "study_version": 1,
  "inputs": {
    "counts": {"kind": "counts", "path": "counts.dat", "orientation": "taxa_by_samples"},
    "cores":  {"kind": "metadata", "path": "cores.csv", "id_column": "core"}
  },
  "datasets": {
    "clean": {"source": "counts", "metadata": "cores", "drop_unmatched_metadata": true,
              "operations": [
                {"op": "exclude", "samples": ["K5"], "reason": "no specimens recovered"},
                {"op": "map_taxa", "mapping": {"globigerina": "Globigerina"}, "reason": "case variant"}]}
  },
  "analyses": [
    {"id": "describe", "dataset": "clean", "spec": {"method": "community", "...": "..."}},
    {"id": "zones", "dataset": "clean", "spec": {"method": "permanova", "...": "..."}}
  ]
}
```

## Preparation operations

The set is closed. Every operation needs a reason, and each one writes a
record.

| Operation | Effect | Refuses |
| --- | --- | --- |
| Input `orientation` | Declares the layout. Derived data are always samples by taxa. | duplicate sample or column IDs |
| `exclude` | Removes the named samples (whole rows). In a measurement table whose column pairs hold different groups, a row removes values from every pair, so give such exclusions their own dataset. | unknown or duplicated IDs; removing every sample |
| `select` | Keeps the named samples, in the order given. | unknown or duplicated IDs |
| `map_taxa` | Renames exact labels. Labels mapped to the same target are summed as exact integers. | unknown labels; merging a missing cell; non-integer cells; use on measurements |
| `exclude_taxa` | Removes named count columns, keeping retained column order, sample IDs and cells. Samples left all-zero are listed (`emptied_samples`) and governed by each analysis's `empty_samples` policy. | unknown or duplicated labels; removing every column; use on measurements |
| Metadata join | Reorders metadata to the dataset by exact ID and renames the declared ID column to `sample_id`. | dataset samples without metadata; metadata rows without samples, unless `drop_unmatched_metadata` is declared, in which case they are listed |

Transformations (`log10` for RMA, relative abundance for community analysis)
stay in the method specification. Those methods already declare and refuse
invalid values, so a separate preparation transform would only duplicate them.
This is a deliberate narrowing of the plan's five operations.

## Row-filter warnings

`exclude` and `select` act on whole rows. For every `rma` analysis, the study
reports each filter that removed complete x/y pairs from that analysis's
columns, as `row_filter_removes_pairs` with the analysis, dataset, columns,
operation index and type, removed rows, pair count and the verbatim reason.
Each operation's removals are counted from its incoming table, so sequential
filters never double-count; rows missing in either column do not count. The
warning asks you to confirm that the filter applies to that analysis. It does
not say the filter is wrong, and it is not inferred from the reason text.

The warnings are returned by `run_study`, saved in `manifest.json`, listed
beside the affected analysis in `report.md`, and recomputed from the saved
inputs by `inspect_study` (and therefore by `reproduce_study`). Method results
are unchanged.

## Bundle

```
study.json            portable study; input paths point at inputs/
inputs/<name>         byte copies of the raw inputs
derived/<dataset>.*   prepared PAST table, aligned metadata, preparation record
runs/<analysis>/<id>  ordinary run bundles
report.md             factual report; each number cites its result field
manifest.json         status, per-step outcome, hashes, run-manifest hashes
```

A failed step is recorded with its error, later steps are marked `not_run`,
and the study status is `partial`, never `complete`.

`inspect_study` checks:

- every hash;
- that each derived file and preparation record recomputes byte for byte from
  the saved inputs;
- that each run bundle verifies;
- that each run's input is exactly its declared dataset, and its saved
  specification is exactly the study's.

`reproduce_study` reruns the whole study from its snapshots and compares every
result under the run-level tolerance policy.

**What integrity checks do not catch.** A study that declares a wrong
exclusion, or a merge of two genuinely different taxa, is internally consistent
and verifies. Judging whether the declarations are scientifically right is the
reviewer's job. The bundle's role is to make every declaration visible and its
consequence recomputable.

## Interfaces

- Python: `run_study`, `inspect_study`, `reproduce_study`.
- CLI: `study-run STUDY --output DIR`, `study-inspect DIR` and
  `study-reproduce DIR --output DIR`.
- MCP: `study_run`, which takes the study inline (input paths must resolve
  inside the session root), `study_inspect` and `study_reproduce`.
