# Independent P07–P12 interim review

Baseline: `71f29d1`; bank introduced at `4bf28f8`. This review covers 12 pilot
items (P07–P12 trap/control) and 4 calibration items (P08–P11), 16 total.

All **38 requested numerical fields agree with the keys**, with maximum
absolute error `2.7755575615628914e-17`. This confirms arithmetic conditional
on the declared handling; it does **not** approve all sufficiency witnesses or
claim the items discriminate between analyst arms.

## Independence record

`recompute.py` read only `materials/*`, hashing all 69 material files. It uses
stdlib-only RMA and Shannon formulas, and exact rational Bray–Curtis distances
and PERMANOVA sums of squares. It never imports `palaeo_agent` or generator/key
code. `predictions.json` and its SHA-256 receipt were saved before any key was
opened, then the seal was reported to the parent agent. The sealed predictions
hash is:

`7b5c493ef2f418303316131544cd5e8f0800b3a8daf3e70ba9dcda4b4b501ca9`

Only afterwards did `compare.py` read `key.json`. It verifies the prediction
seal and material hashes, compares every field and records key hashes and
witnesses. `build_bank.py` remains unread. The scripts refuse to replace their
output records. Sealed predictions retain independently identified assumptions
and alternatives even when the primary values match a key.

## Findings to resolve before freeze

### P08: exact-boundary classification is unspecified

The trap dictionary places the Pleistocene–Holocene boundary at 142 cm. The
pilot has **S10 at exactly 142 cm**, and calibration has **S08 at exactly
142 cm**. Neither gives a sample interval, epoch label or boundary inclusion
convention. The key witness says shallower samples are Holocene, then silently
uses the strict `<142` comparison. It does not establish how the sample exactly
at the boundary is classified.

| Item | Strictly shallower, as keyed | Include the boundary sample |
| --- | --- | --- |
| P08-trap | n=9; mean BC=0.23432878815158759 | n=10; mean BC=0.26759937714050164 |
| P08-cal | n=7; mean BC=0.2649284508518656 | n=8; mean BC=0.2940823193377051 |

These are material differences, not tolerance noise. Both alternatives were
computed before seeing the key. A midpoint sample exactly at a modeled
boundary can also span it; it should not be assigned automatically without an
explicit operational convention. The control has epoch labels and is
unambiguous.

**Recommendation:** remove the boundary-coincident samples from this generator
by placing them clearly on one side, or provide sampling intervals/epoch
classification. If retained, accept a declared convention or unresolved
classification instead of scoring only one numeric vector as scientifically
entailed. This is a validity repair, not extra task difficulty.

Also, every P08 key has `exclusions_expected: []`, although the requested subset
omits 7 pilot samples or 9 calibration samples under the keyed convention.
The answer schema asks for samples left out and reasons. The scorer should
state whether these subset decisions must be reported; an empty key list
cannot check them.

### P12: arithmetic is determined; permutation validity is not

The A/B restriction entails excluding unassigned transition samples; both
keys' F, R² and n recompute exactly. The trap excludes A19, A20 and A22, and
there is no support for treating blank labels as a third group.

However, both dictionaries describe samples from one stratigraphically ordered
section. They supply no sampling or residual-exchangeability statement that
justifies unrestricted label permutations. The task asks to **test** zone
differences using at least 999 permutations, while the requested results contain
only F and R² and no p-value. A correct descriptive calculation therefore cannot
establish that the requested inferential test was completed correctly.

This does not prove the actual samples are dependent. It means the key's
witness proves the subset rule, not the validity of the statistical test. The
independent answer reports deterministic values conditionally and does not
assert valid unrestricted inference. Requiring a definite complete answer can
penalise justified caution, especially when the toolkit requires explicit
design declarations.

**Recommendation:** provide adequate design facts for the intended test and
score the inference, or make the task explicitly descriptive and accept
conditional interpretation. Do not silently treat a missing design declaration
as evidence that independence holds.

### P09: the exclusion is explicitly dictated

The dictionary states that the collection protocol measures one right valve
per individual. Left-valve records also name their corresponding individual.
Selecting right valves is therefore fully determined and the keyed regression
is correct. It is also explicitly coached at the operational level, much like
the earlier D7-control case. It is a useful provenance/data-processing check,
but weak evidence of independent recognition of pseudoreplication.

**Recommendation:** treat it as a control or transparently classify it as
protocol adherence. Do not count a failure to follow the stated protocol as a
hard, uncoached inferential trap without qualification.

## Difficulty and failure signatures

These are pre-trial judgments, not measured agent performance.

| Family | Assessment |
| --- | --- |
| P07 | Low difficulty: the dictionary states mm versus cm. All fields match. Mean length provides a strong unit-error signal; slope and intercept also differ beyond tolerance. |
| P08 | Low/moderate join and subset task, with the exact-boundary validity defect above. |
| P09 | Low difficulty and an explicit protocol instruction. |
| P10 | Low difficulty: given numbering direction, select numeric endpoints and reverse the sign. It tests reading and sorting, not a complex analysis. |
| P11 | Low/moderate mapping and aggregation; the dictionary supplies the exact obsolete/current combination. No taxonomic research is required. |
| P12 | Moderate sequence of ID join, subset, row standardisation and F/R² calculation; inference ambiguity remains. |

All stored wrong-answer signatures in these families differ from at least one
key field by more than 10 times the conservative combined
`abs_tol + rel_tol*abs(expected)` threshold. The weakest is the P11 calibration
Bray–Curtis signal (about 16.6 tolerances); `n_genera` does not distinguish the
obsolete-genus error because both mappings still have five genera. These
separations establish numerical detectability, not expected analyst difficulty.

The bank remains vulnerable to a ceiling because most dictionaries supply a
single direct fact that resolves each preparation decision. Calibration should
be interpreted as a genuine design test, not a formality. No live trials or
model calls were made in this review.
