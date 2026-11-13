# Application 6: draft intake for review

Codex, 13 November 2026. Implements the preparation requested in proposal
revision 2 (`a351379`, Board 3349). **This is not the scientific design
freeze.** Crosswalks, the proposed 0.80 retained-weight floor and the resulting
candidate/representative lists remain subject to Claude's intake review.
No distance, percentile threshold, nearest neighbour or analogue verdict has
been computed. The new `analogue` method and `stack` operation are not built
or bypassed here.

## Preflight finding: do not freeze this as a whole-spectrum comparison yet

The proposed rule exposes a substantial information loss. Conservative
treatment of unresolved broad/narrow categories leaves **69 of 72 fossil
levels below the proposed 0.80 floor**, with retained fractions of recorded
dryland weight ranging from **30.8% to 84.0%**. Only samples **531368,
531369 and 531370**, at archive **395, 400 and 405 cm**, pass. This is a
taxonomy/weight-retention check, not an analogue result.

| Draft scheme | Common bins | Modern rows taxonomically eligible | Modern candidates after 0.80 floor | Calibration representatives | Fossil levels passing floor |
| --- | ---: | ---: | ---: | ---: | ---: |
| Primary | 34 | 61 | 17 | 8 | 3 / 72 |
| Coarse | 22 | 68 | 17 | 8 | 3 / 72 |

The actual candidate and calibration ID sets are **identical** between
schemes at this floor. All seven newly taxonomically eligible genus-only
rows fail it. Naracoopa is one of the eight proposed representatives despite
its separately flagged unresolved source denominator: passing the weight
floor does not resolve source quality. The Cradle Link Road representative
falls back to sample code 6 (1463450), and Tyndall to code 3 (1480881), by
the fixed first-qualifying preference rule.

The main losses include Asteraceae and Eucalyptus, whose complete common
bins would require unresolved broad/narrow pooling. The maps were chosen
before these retained fractions were inspected and were not relaxed in
response. This conservative draft implements the literal evidence rule;
it is not evidence that broader, explicitly assumed recorded-weight pools
would be mathematically invalid.

**Recommendation for the review:** settle the source-bin accounting
assumption before freezing. Earlier worked examples explicitly used archived
category weights with residual-bin assumptions; the revised proposal's
evidence requirement is stronger. If additive recorded categories are accepted
as a working reconstruction, record that assumption and revise the crosswalks
prospectively. If confirmed exclusive counting is required, obtain that
evidence or reconsider the reference/input scope. Lowering the floor alone
does not restore the missing compositional information. No such amendment
or matching was performed in this draft.

`metadata-seed.csv` records all 68 modern samples, their actual collection
units, dataset-level identification resolution, medium/altitude provenance
and preference order for calibration. `sample-ledger.csv` adds the
provisional crosswalk and 0.80-floor decisions. Every excluded candidate
has a reason; every eligible unit's highest-preference qualifying row is
its proposed representative. Shared site coordinates are flags, not an
instruction to merge units. See [metadata-notes.md](metadata-notes.md).

The two complete crosswalks account for every source column exactly once:
[primary](crosswalk-primary.csv) and [coarse](crosswalk-coarse.csv).
Reasons distinguish deliberate dryland exclusions, incomparable categories,
and supported mapping/pooling. The scientific rationale and unresolved
counting-protocol issues are in [taxonomy-notes.md](taxonomy-notes.md).
An identity between archived category labels does not establish botanical
species identity or a shared source denominator.

The primary keeps the two named *Nothofagus* species and excludes the six
genus-only datasets as specified. The coarse scheme pools to genus and
allows those datasets through its taxonomic eligibility rule. Revision 2
therefore permits **both resolution and reference membership** to change,
including calibration. Actual membership must be reported after the floor
is applied: in this conservative draft the resulting ID sets happen to be
identical, as shown above. On original primary-eligible rows, the script
checks that coarsening preserves retained weight exactly and that both
schemes use the same outside-dryland bins.

## Sources and computation boundary

The saved-Neotoma reader is called three times, with explicit dataset lists,
element/ecological-group filters, units and absent-taxa-zero declarations:

| Source | Rows | Columns | Native units |
| --- | ---: | ---: | --- |
| Lake Selina 52767 | 72 | 66 | NISP |
| Tasmanian percentage datasets | 61 | 92 | percent |
| Hartz 74305 and Tyndall 74913 | 7 | 82 | NISP |

All extraction bundles inspect as verified and each table matches the prior
application's table. Original units/numbers are preserved. Raw and mapped
tables under `data/` are **unnormalised weights**; no stack or distance is
constructed. Study `exclude_taxa` and `map_taxa` operations implement every
declared exclusion and merge. Their records are in `derivation-records.json`.
Community `validate` checks applicable nonempty subsets without calculating
distances or ordination. Empty mapped rows remain in the saved inputs and
ledgers with explicit status; they are excluded only from structural
validation when that operation cannot accept them. A standalone one-row supplement is not treated as a community
ordination: its full source table is validated, then its selection and mapping
are checked.

`prepare.py` guards the toolkit's distance/analysis entry points with
exceptions, tests the guard, and requires zero subsequent calls. Extraction,
study preparation and structural validation run inside that guard. This is
a guard on the used code paths, not an operating-system sandbox.

| Subtask outside a suitable public operation | Why | Implementation and check |
| --- | --- | --- |
| Per-sample metadata interpretation and identification-resolution audit | The reader copies metadata; it does not interpret collection notes or analyst resolution | Source-keyed seed ledger, dataset-wide bin audit, explicit uncertainty |
| Retained-weight partition and ratio during no-distance intake | The public community calculation supplies totals together with distances/ordination; no suitable totals-only operation exists for this stage | Exact decimal-to-rational accounting; source = outside-dryland + incomparable + retained; API merge totals must agree exactly |
| Provisional candidate and representative assignment | The new matching operation is not yet implemented, and eligibility is a scientific intake rule | Explicit taxonomic/floor predicates and first qualifying metadata preference per unit; all IDs/reasons exported |
| Canonical column order and report CSVs | Formatting of derived fields | Identical target sets required; ordering recorded in file headers; no missing column filled with zero |

The scalar retained fraction is retained recorded weight divided by the
declared dryland recorded weight. Deliberately excluded wetland/aquatic
weight is reported separately from incomparable dryland weight. Exact
rational values accompany display decimals in `coverage.csv`; the 0.80
comparison uses the exact value. It is **not** a guarantee that 80% of grains
or ecological information are represented. Naracoopa's unresolved percentage
denominator remains flagged, independently of whether its fraction passes.
No source-unit repair or new source-quality exclusion is inferred here.

All 72 fossil IDs occur in `fossil-ledger.csv`, including any below-floor
`taxonomy_limited` levels. A zero retained row is distinguished as
`empty_retained_row`, since it cannot be normalised for matching. The accepted
reconstructed 531331 row is prepared separately, with both crosswalks, from
the previously saved `counts-final.tsv`. Its only retained-source cell change
is the documented 0→72 *Lagarostrobos* count. That source is already dryland;
its coverage record does not claim to reconstruct earlier out-of-sum loss.

## Checks and regeneration

```bash
uv run palaeo-agent primer
uv run analyses/lake-selina-analogues/prepare.py
uv run analyses/lake-selina-analogues/audit.py
# Independent destination for checking deterministic preparation:
uv run analyses/lake-selina-analogues/prepare.py --output /tmp/selina-intake-check
```

The full primer was read and its unchanged version checked before preparation:
**0.2.0.dev0**, SHA-256
`fcc02a57db1ffa2a86d14e7c2540bd7bfa89c14e7e5b3334286f9a24b16747f6`.

`preflight-check.json` records bin coverage, exact weight invariants, validation
warnings/refusals, provisional candidate/representative IDs and output hashes.
It is a preparation receipt, not a claim of analytical or ecological validity.
Transient extraction bundle paths and manifest hashes are separate in
`intake-provenance.json`; native bundles are ignored by Git. No original
application file is changed.

All ten applicable raw/mapped multirow validations pass, with no warnings.
Both single-query validation entries are marked not applicable to community
ordination. Regeneration into a fresh destination gives identical bytes for
all **16 deterministic preparation artifacts** and an identical preflight
receipt; extraction UUIDs are deliberately separate. See
[replay-check.json](replay-check.json). A separate read-only arithmetic audit
checked all **282 accounting rows and 7,896 mapped cells** without a mismatch.
Its executable check and receipt are [audit.py](audit.py) and
[audit-check.json](audit-check.json); it shares no accounting functions with
the preparation script.
It also found two script gaps, now repaired: empty mapped rows are reported
before subset validation, and the dryland denominator cannot drift between
schemes. A synthetic zero-row check confirms the reporting path while the
distance function is guarded. These fixes did not alter the real intake
counts above.

After intake review, one coherent freeze must fix the floor, eligibility,
representatives, crosswalks and executable analysis design before any real
matching or threshold preview. A numerically valid intake can still be
scientifically inadequate; low retained weight or unresolved source bins are
review findings, not reasons to silently change this draft.
