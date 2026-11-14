# Application 6: whole-tally crosswalks, revision 2.1

Codex, 14 November 2026. These drafts implement proposal revision 2.1
(`f0a33a6`, Board 3382). They supersede the conservative crosswalks in
**0bb8cb7**; that commit preserves the earlier mappings and their rationale.
The earlier coverage preflight had been seen and prompted the revision.
This redraft follows the approved tally convention and scientific scope
before inspecting any revised coverage, distance, threshold or match.
It is an intake-review classification, not the frozen application design.

Both CSVs account for all 240 source labels exactly once: fossil 66,
modern percentage 92, and modern NISP 82. The primary has **46 shared
bins** and the coarse mapping **30**, with the same target set explicitly
formed in all three source tables. These are structural label counts,
not scientific outcomes. The sample ID column is not a pollen category.

## What the additive convention does and does not establish

Each archived variable is treated as a separate additive tally. Whole
source tallies are assigned to one target or excluded; none is split,
subtracted, apportioned between species or manufactured as a new zero
column. Counts remain counts and percentages remain their archived weights
at this preparation stage. Row closure belongs to the eventual analysis.

The saved sum check tests a necessary implication of a joint hypothesis:
if a broad tally includes the selected narrower tallies, those children are
disjoint, and all use the same numerical base, broad must be at least their
sum. A violation rejects that joint interpretation. The independent audit
also tests broad against the largest single child, avoiding the assumption
that children are disjoint. On the same positive-cooccurrence subset the
sum and single-child tests give contradictions in 31/49 and 30/49 tested
dataset/bin combinations, respectively. Neither test establishes a common
percentage denominator. The narrower list need not cover every relative
to supply a single-child counterexample.

That inequality **does not prove universal disjointness**, exclude partial
overlap or inconsistent definitions, verify a common percentage denominator,
or transfer a result automatically to another dataset or pollen group.
A non-violation is consistent with either inclusion or separate tallies.
Additivity remains the **approved working convention**, supported by the
qualified rejection of full inclusion where testable and assumed elsewhere. Eucalyptus,
for example, is pooled under the convention even though its tested NISP
rows did not contradict inclusion. Asteraceae pooling likewise does not
claim a positive disjointness proof from absent co-occurrences.

The crosswalks do not repair the modern denominator problems. The parent
ledger separately flags those and applies the approved calibration rule.
Neither a crosswalk nor row closure proves consistent identification effort
or counting bases across the archived analysts.

## Shared primary classification

The two Nothofagus species stay separate. Genus-only modern Nothofagus is
excluded in the primary CSV and never allocated to species. The parent
ledger must also enforce the six fixed whole-dataset exclusions: 75430,
74779, 74795, 74777, 75423 and 75421. The CSV alone does not establish
primary dataset eligibility.

**Eucalyptus** is separate, with its species tally pooled upward where
present. **Asteraceae** pools family, subfamily and Taraxacum tallies
because the fossil family tally cannot be split into subfamilies.
**Cupressaceae** keeps Athrotaxis/Diselma whole and pools it with the
recorded family/genus tallies; it is not allocated between the genera.
Casuarina and Allocasuarina similarly meet at Casuarinaceae rather than
being asserted to be genus synonyms. Apiaceae, Caryophyllaceae and Rosaceae
use the whole-family unions their three different recorded resolutions
can form. Gentiana/Gentianella, Brassica, Didymotheca and Drimys/Tasmannia
meet at their documented common families.

Some shared named bins remain separate because every source can also form
an explicit recorded residual. The residuals are:

| Primary residual target | Fossil whole tallies | Modern percent whole tallies | Modern NISP whole tallies |
| --- | --- | --- | --- |
| Other Ericaceae | Epacrideae | Epacrideae; Ericaceae; Leucopogon | Epacrideae; Epacris; Ericaceae cf. Archeria |
| Other Myrtaceae/Melastomataceae | Melaleuca; Myrtaceae cf. Baeckea | Callistemon; Leptospermum/Baeckea; Melaleuca squamea; Melaleuca-type; Melastomataceae/Myrtaceae; Myrtaceae | Baeckea; Melaleuca; Melaleuca squamea |
| Other Proteaceae | Cenarrhenes nitida; Hakea; Proteaceae | Hakea; Lomatia; Persoonia; Proteaceae | Persoonia |
| Other Rhamnaceae | Spyridium | Rhamnaceae; Spyridium | Rhamnaceae |
| Other Rutaceae | Phebalium squameum; Rutaceae | Correa; Phebalium; Rutaceae | Rutaceae |
| Other Podocarpaceae | Microcachrys tetragona; Phyllocladus aspleniifolius; Podocarpus lawrencei | Microcachrys; Phyllocladus; Podocarpaceae; Podocarpus | Microcachrys; Phyllocladus; Podocarpus |

“Other” means a **recorded-tally union**, not a guaranteed biological
complement. Broad or uncertain residual tallies can contain unassigned
grains of the separately retained genera. In particular, the other
Myrtaceae/Melastomataceae bin may contain unassigned Eucalyptus and
Leptospermum, and the other Podocarpaceae bin may contain unassigned
Pherosphaera and Lagarostrobos. Nothing is subtracted from a broad tally
using a separately counted narrower value.

The modern Melastomataceae/Myrtaceae composite explicitly spans families;
its target is never labelled wholly Myrtaceae. Leptospermum/Baeckea and
Athrotaxis/Diselma are within-family composites, but also remain whole.
The fossil cf.-Baeckea label is not promoted to a verified Baeckea genus.

The shared **Pherosphaera** target preserves the proposal's genus-level
Pherosphaera/Microstrobos convention without a modern species upgrade.
The shared **Lagarostrobos** target is retained for the pre-existing
basal-forest question, with Dacrydium franklinii treated as its verified
species synonym before genus pooling. The other podocarp union deliberately
loses the finer Microcachrys/Phyllocladus/Podocarpus distinctions. This is
a fixed scientific scope choice made before revised coverage or matching,
not a claim of a mathematically unique finest partition.

Acacia/Fabaceae and Amperea/Euphorbiaceae are instead pooled to their full
recorded family unions: the NISP table has no independent residual tally
that could remain after separating those genera. No empty residual column
is invented merely to preserve a narrower target.

## Conservative exclusions still required

The same paper-informed dryland rule applies in both schemes: Cyperaceae
and its named sedge descendants (Baumea, Carex, Eleocharis, Gymnoschoenus),
Restionaceae including Centrolepis under current placement, Xyridaceae,
Portulacaceae and Ranunculus are outside the declared sum. This is a
comparative denominator convention, not a claim that all relatives are
aquatic. Modern Ranunculaceae cannot be split to remove Ranunculus and
therefore remains **incomparable**, not classified wholesale as aquatic.
NISP Anemone is an unshared named bin, also incomparable.

By the parent scope decision, legacy Liliaceae/Milligania/Iridaceae/Isophysis
and Scrophulariaceae/Myoporum/Euphrasia remain incomparable in both schemes.
There is no supported common circumscription for a new monocot or legacy
Scrophulariaceae catch-all. Shared Astelia remains a named genus bin;
excluding the legacy variables does not reconstruct their unidentified
content. Other unmatched named bins remain excluded when no justified
shared natural union exists. Additivity alone is not permission to combine
unrelated bins solely to increase retained mass.

## Coarse mapping and application order

Coarse is a function of retained primary bins:

| Coarse target | Primary bins pooled |
| --- | --- |
| Proteaceae | Agastachys; Banksia; Bellendena; Orites; Telopea; Other Proteaceae |
| Podocarpaceae | Lagarostrobos; Pherosphaera; Other Podocarpaceae |
| Ericaceae | Monotoca; Richea; Sprengelia; Other Ericaceae |
| Cunoniaceae | Bauera; Eucryphia |
| Rutaceae | Boronia; Other Rutaceae |
| Myrtaceae/Melastomataceae | Eucalyptus; Leptospermum; Other Myrtaceae/Melastomataceae |
| Rhamnaceae | Pomaderris; Other Rhamnaceae |
| Nothofagus | Nothofagus cunninghamii; Nothofagus gunnii |

All other retained primary bins remain unchanged. The sole additional
source bin is modern percentage Nothofagus, admitted to the genus target
for the newly eligible datasets. No other exclusion is reversed. Thus
retained source tallies are identical on existing primary-eligible rows,
provided the parent ledger checks that the excluded genus-only bin is
absent there. The retained-mass consequence is checked by the parent,
not used to choose these mappings. The larger coarse collection also
changes candidates and calibration representatives as declared in revision
2.1; verdict differences cannot be attributed to taxonomy alone.

Apply source-label exclusions **before** mapping and use one whole-tally
mapping per input table. Do not exclude a source name after it has become
a shared target. The source and target sets have been checked structurally
without reading numerical row weights. A synonym followed by upward pooling
is marked synonym with both actions in its reason; uncertain/composite
identifications retain that provenance under coarse pooling.

## Evidence keys

Botanical pages were consulted on 13–14 November 2026. They verify names or
parentage, **not** the archived analysts' grain-counting protocols. No
third-party source prose is reproduced here.

| Key | Evidence and scope |
| --- | --- |
| HEADERS | Line 1 of `../lake-selina/data/counts.tsv`, `../tas-surface/data/percent.tsv`, `../pollen-media/data/counts.tsv`; labels only. |
| BINOMIAL_RULE | Individually declared upward mappings of named species to their own genus; uncertain/composite labels are not parsed as binomials. |
| COMMON_TARGET_RULE | All three source tables must have an explicit, compatible recorded target. Header absence is not repaired with zeros. |
| DRYLAND | `../lake-selina/AMENDMENT-1.md`, paper-informed denominator section; application-6 revision 2 extends the rule to descendants. |
| HISTORICAL_EXCLUSIVITY_GAP | `../lake-selina/INTAKE.md`, residual-category assumption; `../tas-surface/REPORT.md`, archived category/denominator caveats. These do not establish exclusive counting. |
| NISP_LABEL_SCOPE | Saved `../tas-surface/source/neotoma-tas-surface-download.json`, datasets 74305 and 74913, sample `datum[].variablename` memberships. No datum values were used. |
| NOTHOFAGUS_RULE | Application-6 proposal revision 2.1, species-resolved primary and genus-only dataset eligibility; parent ledger enforces it. |
| PHEROSPHAERA | [UTAS key](https://dicotkey.utas.edu.au/dicotkey/CONIFERS/sPhaerosphaera.htm), [USDA Microstrobos species list](https://npgsweb.ars-grin.gov/gringlobal/taxon/taxonomyspecieslist?id=7613&type=genus): the older genus contains names now assigned to Pherosphaera; genus-only modern identification remains genus-only. |
| LAGAROSTROBOS | [Kew taxon record](https://powo.science.kew.org/taxon/910807-1): Dacrydium franklinii is the species synonym of Lagarostrobos franklinii. |
| BRASSICACEAE | [Royal Botanic Gardens Victoria / NSW flora key](https://keybase.rbg.vic.gov.au/keys/4635): Brassica is included within Brassicaceae. |
| GENTIANACEAE | [Kew family treatment](https://powo.science.kew.org/taxon/urn%3Alsid%3Aipni.org%3Anames%3A30000253-2/general-information): both Gentiana and Gentianella belong to the family. |
| GYROSTEMONACEAE | [USDA family genus list](https://npgsweb.ars-grin.gov/gringlobal/taxon/taxonomygenuslist?id=503&type=family): Didymotheca is assigned to Gyrostemonaceae (as a synonym of Gyrostemon). |
| WINTERACEAE | [Kew Tasmannia record](https://powo.science.kew.org/taxon/urn%3Alsid%3Aipni.org%3Anames%3A555234-1), [USDA Drimys record](https://npgsweb.ars-grin.gov/gringlobal/taxon/taxonomydetail?id=14692), and [generic-separation study](https://doi.org/10.3732/ajb.91.3.321): shared family placement, with generic distinction preserved by upward pooling. |
| CYPERACEAE | [ANU Australasian Pollen and Spore Atlas family index](https://apsa.anu.edu.au/samples/browse.php): Cyperaceae includes Baumea, Carex, Eleocharis and Gymnoschoenus. |
| CENTROLEPIS | [NSW Flora Online genus treatment](https://plantnet.rbgsyd.nsw.gov.au/cgi-bin/NSWfl.pl?lvl=gn&name=Centrolepis&page=nswfl), [Kew genus record](https://powo.science.kew.org/taxon/urn%3Alsid%3Aipni.org%3Anames%3A6717-1): current Restionaceae placement. |
| ADDITIVE_TALLIES | Proposal revision 2.1 (`f0a33a6`, Board 3382), and `../../references/independent/2026-11-14-tally-semantics/check.py` / `receipt.json`; the inclusion test challenges a universal inclusive-total interpretation, while additivity remains a declared working convention. |
| FAMILY_PARENTAGE | Explicit source-label groups in the CSVs; [ANU pollen-family index](https://apsa.anu.edu.au/samples/browse.php) supplies the familiar genus/family placements. [NSW Acacia treatment](https://plantnet.rbgsyd.nsw.gov.au/cgi-bin/NSWfl.pl?lvl=gn&name=Acacia&page=nswfl) confirms Fabaceae; [VicFlora Rhamnaceae key](https://vicflora.rbg.vic.gov.au/flora/key/2478) includes Pomaderris and Spyridium. Botanical parentage does not establish tally exclusivity. |
| LEGACY_SCOPE | Parent scientific scope decision, 14 November 2026: keep legacy Liliaceae/Milligania/Iridaceae/Isophysis and Scrophulariaceae/Myoporum/Euphrasia incomparable rather than invent unsupported shared unions. The dryland Ranunculus rule also cannot be applied by splitting modern Ranunculaceae. |
| COARSE_PARTITION | The current coarse table above; [ANU index](https://apsa.anu.edu.au/samples/browse.php) verifies the selected Proteaceae and Podocarpaceae genera; [Missouri Botanical Garden APweb](https://www.mobot.org/MOBOT/Research/APweb/genera/cunoniaceaegen.html) includes Bauera and Eucryphia in Cunoniaceae. Current Ericaceae placement is supported by [NSW Monotoca](https://plantnet.rbgsyd.nsw.gov.au/cgi-bin/NSWfl.pl?constat=&dist=&lvl=gn&name=Monotoca&page=nswfl&showsyn=), [Kew Richea](https://powo.science.kew.org/taxon/331910-2) and [University of Sydney Sprengelia](https://eflora.sydney.edu.au/taxon/sprengelia). |

The crosswalk author completed these choices without computing or inspecting
revised retained-mass ratios, distances, thresholds or matches. The parent
subsequently applied the CSVs through study operations and ran the retained-
weight audit; its results are in INTAKE.md. Matching remains uncomputed.
