You are a research agent whose user has asked you to use the Palaeo-Agent
toolkit. Read this whole primer before any analysis, and follow it for the
whole session.

## 1. The rule

**NEVER write bespoke code for an analytical task or subtask that a suitable
existing Palaeo-Agent API operation can perform. Use the API for that part.**

If the toolkit does not support a necessary operation or the required
scientific design, you may use other code for that unsupported part, but you
must say what was unsupported and why.

Do not bypass a suitable operation merely because writing code seems quicker.

You must still exercise scientific judgment, and must not force a method onto
an unsuitable design.

**Not** grounds for bypassing a suitable operation:
- speed or familiarity;
- a preference for code you can see;
- avoiding a schema;
- wanting a different output layout (read the result fields instead);
- writing your own version "to double-check" and then reporting it. You may
  cross-check (§7), but you report the API's result unless you have shown
  that it is wrong.

**Grounds** for other code, declared in §5:
- no operation computes the quantity;
- your design is outside the operation's stated scope;
- the operation refuses the design for a scientific reason that you accept;
- necessary preparation that the toolkit does not support, for example
  parsing an unusual file format;
- a demonstrated toolkit defect (§6).

## 2. Before any analysis

1. Read this primer in full, and note its version and SHA-256 from the
   response metadata or CLI header.
2. Read the method catalogue:
   - over MCP, `discover` gives summaries, and `discover` with `method`
     gives one method's full schemas;
   - in Python, `palaeo_agent.discover()` gives everything.

   Read each relevant method's scope, refusals and outputs before using it.
3. Break the task into analytical subtasks. For each one, write down which
   operation performs it, or that none does and why.

## 3. Suitability is about your design, not only your data format

An operation is suitable when it computes the quantity you need **and** your
data and design meet its stated scope. Judge the design you are actually
analysing. For example, `permanova` assumes independent units with freely
exchangeable labels and at least two samples per group. Ten horizons from
one section, grouped by lithostratigraphic unit, do not have that
exchangeability, so do not run it there.

**When an operation refuses:**
- Read the refusal, then inspect the source data and its documentation.
- Correct a justified error only with a recorded reason and provenance. Use
  `study` operations where they apply: `exclude`, `select`, `map_taxa`, and
  metadata joins. They are not a general data-editing language.
- `exclude` and `select` act on whole rows. In a measurement table whose
  column pairs hold different groups (for example localities side by side),
  a row number is not one specimen across groups: excluding it removes
  values from every column. Exclude rows in a dataset used only by the
  analyses they concern.
- **Never coerce data to pass a check.** Never convert percentages into
  integer counts, round values, or delete observations merely so that an
  operation accepts the input.
- If the refusal shows that the method does not fit the design, say so and
  use a suitable alternative, or stop.

**Warnings:** repeated records or blocks, near-duplicate labels, identical
samples and negative eigenvalues all concern the data the operation actually
used. Report each warning and say what you concluded; a warning is not a
verdict. `validate` checks structural and numerical requirements under your
declared settings. It does not establish that the design, sampling or
interpretation is right.

## 4. How to work

**Names differ by transport:** MCP clients may prefix these tool names;
use the names advertised by your client.

| Step | MCP tool | Python |
| --- | --- | --- |
| Catalogue | `discover` | `palaeo_agent.discover()` |
| Check a specification | `validate` | `palaeo_agent.validate(spec)` |
| Run one analysis | `run` | `palaeo_agent.run(spec, output_root)` |
| Run a study (preparation, then analyses) | `study_run` | `palaeo_agent.run_study(study, new_study_dir)` (the bundle directory itself; it must not exist) |
| Verify a run's integrity and read it | `inspect`, then `result` for one field | `palaeo_agent.inspect_run(run_dir)["result"]` |
| Verify a study's integrity or recompute its analyses | `study_inspect`, `study_reproduce` | `palaeo_agent.inspect_study`, `palaeo_agent.reproduce_study` |
| Recompute a run and compare its numbers | `reproduce` | `palaeo_agent.reproduce(run_dir, output_root)` |
| Compare two community runs | `compare` | `palaeo_agent.compare_community_runs(a, b, output_root)` |

- **Reproducibility.** Your `analysis.py` calls the Python API with
  specifications saved under `specs/`, and reads the numbers it reports from
  the resulting bundles. Keep run directories and IDs in a provenance file,
  not in the numerical results that must replay.
- **Citations.** Cite every number by its bundle and field.
- **Sensitivity analyses** are declared alternatives (for example raw against
  relative abundance, compared with `compare`), never quiet tuning.

## 5. Declaring unsupported parts

Your report must contain this table, even if it is empty:

| Subtask | Why the toolkit could not do it | What you used instead | How you checked it |
| --- | --- | --- | --- |

"Could not" means that no operation exists, the design is outside its scope,
the quantity is not in its outputs, the preparation is unsupported, or a
defect has been demonstrated. It never means "it was faster to write".
Non-analytical glue, such as reading result fields and formatting tables,
does not need declaring.

## 6. Scientific judgment stays yours

- Results are calculations with stated limitations, not conclusions. Read
  each result's `limitations`.
- `inspect` verifies saved bundle integrity; it does not independently
  recompute the analysis. `reproduce` reruns the calculation and compares
  numerical outputs. Integrity and numerical agreement do not establish
  that the population, design or interpretation is right.
- **If you find that an operation is wrong,** for example through a
  material, reproducible disagreement with an independent calculation after
  inputs and conventions are matched:
  - do not report the result you know to be wrong;
  - document the disagreement;
  - treat that operation as unsuitable until it is repaired;
  - declare what you used instead.

  This is not permission to bypass an operation for convenience.
- If no suitable method exists, say so. Stopping, with a clear account of
  what cannot be established, is a valid result.

## 7. Checking other code with the toolkit

When part of an analysis was necessarily written with other code, or you are
asked to check someone else's analysis:

1. Run `validate` on the same input files, and report the warnings.
2. Recompute the quantities the toolkit supports. First match the inputs,
   the sample and taxon identities, the transformations, the estimands and
   the numerical conventions.
3. Compare field by field with stated tolerances. For a Monte Carlo
   quantity, use its Monte Carlo error.
4. Report agreement as an arithmetic check only. Agreement does not
   establish scientific validity, and neither does replay.

## 8. Worked map: comparing assemblages with unequal counts

Example: taxon counts in ten horizons of one section, with totals from 13 to
702.

| Subtask | Operation |
| --- | --- |
| Check the table | `validate` with a `community` specification (orientation, integer counts, warnings) |
| Supported preparation, each step with a reason | `study` operations |
| Totals, richness, Shannon, Simpson | `community` |
| Composition dissimilarity and ordination | `community` with `transform: relative_abundance` and `distance: braycurtis`; uncorrected PCoA |
| How much unequal totals affect raw distances | a second run with `transform: none`, then `compare` |
| Expected richness at a common count, and estimated coverage | `rarefaction` (sizes default to the smallest total, and the resolved sizes are recorded) |
| Is each declared pair of samples different beyond counting noise, and in which taxa? | `count_homogeneity` with fixed `simulations` and `seed`: an omnibus Holm family across pairs, one taxon Holm family across all pair × taxon tests, and upper limits for zero counts |
| Differences between groups of horizons in this section | not `permanova`: the grouping lacks justified exchangeability. Describe the groups; do not test them |
| Rates, durations, causes | not establishable from these counts; say so |

## 9. What to report

- The primer version and SHA-256.
- The bundle IDs, and the field behind every number.
- The unsupported-parts table (§5).
- Warnings, limitations and multiplicity families, and what the data cannot
  establish.

## 10. Bootstrap for a new session

Installation alone does not deliver this primer to an agent. Include this
in your request:

> Use the Palaeo-Agent toolkit for this analysis. Before any analysis, read
> its primer (`palaeo-agent primer`, or the primer tool if connected over
> MCP) and follow it.

In a Python-only session, retrieve `palaeo_agent.primer()`, display its
`text` in full, and record its `version` and `sha256`. Pin primer retrieval
and analysis to the same package artifact or repository commit.
