# Saved-Neotoma reader implementation review

Codex (`gpt-6.1-sol`), 8 November 2026. Reviewed `6f17b50`.
Production code, tests and demonstrations are unchanged by this review.

**Both real-source demonstrations pass. Repair the six issues below before
accepting the reader for general use.** None changes the supplied examples'
tables or numerical results.

## P1: MCP advertises an impossible extractor request

At `src/palaeo_agent/mcp_server.py:114–116`, `_schema` replaces every
property named `spec` with the scientific-method schema. Live stdio
`list_tools` therefore advertises `neotoma_extract.spec.method` as required,
with the five scientific methods as its allowed values. `NeotomaSpec`
forbids that field and the extractor has no scientific method discriminator.

A correct request without `method` succeeds when sent directly. Adding the
advertised `method: "community"` returns `invalid_request` / `extra_forbidden`.
No request satisfies both the advertised and implemented schemas. Preserve
the actual Neotoma schema; restrict method-schema compaction to the
scientific requests. Add a live advertised-schema/request agreement check.

## P2: JSON conversion can erase positive observations

At `neotoma.py:111`, ordinary `json.loads` converts numeric `1e-400` to
`0.0` before `_value` can inspect it. A percentage extraction completes,
inspects as verified and passes downstream abundance validation with that
positive value erased. The first sample's API richness is then 1, although
the source has two positive categories. This reopens the source-fidelity
problem that sprint 11 closed for direct analytical inputs.

Preserve enough precision while parsing to detect positive-to-zero
conversion, and return a structured numerical refusal when the value cannot
be represented safely. At `neotoma.py:98`, a percentage integer of 10**400
also leaks `OverflowError` from `math.isfinite`; translate conversion/range
failures into the declared refusal. Do not silently coerce the source.

## P2: manual TSV output can change taxon identity

At `neotoma.py:188–190`, joining labels with tabs does not quote TSV fields.
Tab and newline labels produce tables that downstream validation refuses,
while the extraction itself inspects as verified. A source label consisting
of literal quotes around `Pinus` is more serious: `taxa.csv` retains
`"Pinus"`, but the table parser reads `Pinus`, and the analytical run succeeds
with the changed label.

Write TSV with proper quoting and verify exact label preservation through
the supported table reader. If a character is unsupported downstream, refuse
it explicitly rather than emitting a completed but unusable bundle.

## P2: required datum types are not checked

At `neotoma.py:154–159`, the required datum fields are tested only for
presence. `element: []` and `ecologicalgroup: {}` leak raw `TypeError` during
set membership. A consistent `taxonid: {"bad": 1}` is accepted and exported.
The contract promises `invalid_source` for wrong required-field types.

Check required types before filtering and identity comparison, with the
same explicit null treatment used for real nullable fields. Add focused
regressions for these demonstrated cases; no general schema framework is
needed.

## P2: the manifest itself escapes bundle validation

At `neotoma.py:270–281`, the inspector validates the listed artifacts but
does not reject a symlinked `manifest.json`. Replacing it with a symlink to
an external manifest still yields `verified`, so the claimed self-contained
bundle depends on an external file. A JSON list instead of an object raises
raw `AttributeError`; `schema_version: true` is accepted as version 1.

Reject a symlinked manifest and validate its object shape and schema-version
type before indexing it. Return `invalid_bundle` for malformed manifests,
as the existing scientific-run inspector does for analogous failures.

## P2: environment claims a lockfile that was not captured

At `neotoma.py:257`, `_environment(_find_lockfile())` records
`available: true`, `path: "uv.lock"` and "Project checkout lockfile captured".
The new bundle neither copies `uv.lock` nor lists it in its manifest. Live
inspection verifies this false provenance record.

Capture and hash the discovered lockfile using the existing run-bundle
convention, and check its presence against the environment declaration.
An unavailable lockfile must be recorded honestly. Keep this conditional
file separate from the deterministic derived-file comparison.

## What passes

- Full suite: **764 passed, 11 skipped** in 88.73 seconds. The process
  cleanup test ran; optional native confinement tests were not enabled.
- **Surface:** all **5,612 cells** match the saved source exactly by sample
  ID and label: 1,370 retained values and 4,242 zero fills. The prior table
  matches by identity; only row order changes. Regenerated `samples.csv`
  and `study.json` are byte-identical to both current and pre-reader files.
  Selection remains 25 records, split 11/14.
- **Selina:** all **4,752 cells** match: 1,891 retained values and 2,861 zero
  fills. `table.tsv` and the regenerated `extract-check.json` are
  byte-identical to their frozen counterparts.
- Every field in the **133 × 22** sample metadata cells and **158 × 8**
  taxon metadata cells matches the sources, including nulls, canonical JSON,
  notes, identities, positive-sample counts and shared-coordinate flags.
  Point and Polygon handling is correct for these sources.
- All **61 surface** and **144 Selina** age rows match the archive and
  specified ordering. Defaults are correct: 61 surface defaults and 72
  Selina IPPD-2 defaults. Selina ages/bounds also match `levels.csv`.
- Fresh surface study execution, inspection and report generation reproduce
  current `results.json` byte for byte. Compared with the pre-reader file,
  the sole change is `/primer/sha256`; numerical results are unchanged.
- Live stdio MCP extraction, inspection and reproduction work for a correct
  direct request. Inspection/reproduction work after deleting the external
  source. Outside-root paths are refused. These successful calls do not
  resolve the advertised-schema defect above.

The earlier five contract clarifications are implemented. Keep that scope;
these are focused repairs, not a request for another feature tranche. The
known verbose MCP inspection response is a minor follow-up, not an acceptance
blocker. The Lake Selina analytical scripts were not rerun: this review
checked the extracted table and ages, not a new ecological analysis.

## Evidence and scope

Primer **0.2.0.dev0**, SHA-256
`bea68f9f65925dcbe4aeeeb2ccb7b74a0915ac4c8ce856e1b49b2e038271d5ac`,
read in full. Supported extraction, inspection, reproduction, validation
and analysis used the public API. Source-field comparisons, adversarial
fixture generation and byte/field comparisons are unsupported review tasks;
they do not replace reported toolkit calculations or establish ecological
validity.

The independent input probes and demonstration audit were reviewed alongside
the parent's live MCP and bundle checks. Compact receipts and reproducible
probes are in
[`references/independent/2026-11-08-neotoma-reader/`](../references/independent/2026-11-08-neotoma-reader/checks.json).
Run these from the repository root, supplying two new scratch directories:

```bash
uv run references/independent/2026-11-08-neotoma-reader/audit_inputs.py /tmp/neotoma-input-audit
uv run references/independent/2026-11-08-neotoma-reader/audit_transport.py /tmp/neotoma-transport-audit
```
