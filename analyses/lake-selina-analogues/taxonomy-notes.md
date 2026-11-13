# Application 6: conservative crosswalk drafts

Codex, 13 November 2026. Drafts for the intake review under proposal revision
2 (`a351379`, Board 3349). These mappings were chosen from headers, source
label scopes and botanical evidence before inspecting retained mass or any
distance. They are not the frozen application design.

Each CSV accounts for every pollen column once: fossil 66, modern percentage
92, modern NISP 82. The primary has 34 shared target bins and the coarse
partition has 22. Every target occurs explicitly in each source's mapping;
no absent taxon column is manufactured or zero-filled. The source ID column
is not a pollen category and is not mapped.

## Meaning and application order

Apply **source-label exclusions before `map_taxa`**. For example, the coarse
target `Proteaceae` is formed from retained named genera, while the source
column called `Proteaceae` is excluded. Excluding source names after mapping
would incorrectly remove the newly formed target.

The crosswalks harmonise recorded identification bins. They do not prove
uniform identification effort, reconstruct unidentified grains, or claim
that genus-only modern pollen identifies a particular species. Explicit
binomial-to-genus decisions are listed individually; no script takes the
first word of an arbitrary label. `cf.`, `-type` and slash-composite labels
are not stripped to create false identifications.

`mapping_kind` identifies the principal operation. A synonym followed by
upward pooling is marked `synonym`, with both actions stated in its reason.
For an excluded row, `uncertain` marks unresolved compatibility or counting
semantics; `identity` marks a recognised source category excluded by the
dryland or common-target rule. Exclusion is not evidence that a label is
biologically invalid.

## Primary partition and its evidence gaps

The two *Nothofagus* species stay separate. The modern percentage source's
genus-only `Nothofagus` is excluded as incomparable, never allocated between
species. This CSV is **not** a substitute for the proposal's whole-dataset
eligibility rule: the parent ledger must exclude the six genus-only datasets
before the primary analysis. This task did not independently re-audit their
values or eligibility.

Some familiar names can be matched without summing nested bins:

- The source NISP label `Atherosperma` belongs to dataset 74305, whereas
  `Atherosperma moschatum` belongs to 74913. Mapping both to the genus cannot
  add the two source labels within one input row.
- Likewise, NISP `Lagarostrobos franklinii` is in 74305 and its verified
  synonym `Dacrydium franklinii` in 74913. Both map to genus-level
  `Lagarostrobos`, without a within-row synonym sum.
- `Microstrobos` and the fossil *Pherosphaera hookeriana* map to genus-level
  `Pherosphaera`. This does not promote the modern genus to that species.
- *Gentiana* and *Gentianella* are different genera pooled to Gentianaceae;
  *Brassica* is pooled to Brassicaceae; *Didymotheca* to Gyrostemonaceae.
  These are upward groupings, not claims that a genus is a family synonym.
- `Drimys`, `Tasmannia` and the fossil *T. lanceolata* are pooled to
  Winteraceae. A genus-only `Drimys` identification is not silently renamed
  to a particular *Tasmannia* species.

There is no adequate protocol evidence in the saved project documents that
all broad and narrow variables are exclusive counted categories. The
earlier Lake Selina intake explicitly treated this as an assumption;
some examples argue against interpreting broad columns as complete family
totals, but do not establish one uniform protocol. The modern report also
retains an unresolved percentage-denominator problem. Neither observation
proves that the archive double-counted individual grains.

The drafts therefore **do not sum unresolved broad/narrow groups**. This
conservatively drops Asteraceae, Apiaceae, Caryophyllaceae, Casuarinaceae,
the Athrotaxis/Diselma–Cupressaceae combination, Eucalyptus, Melaleuca,
Plantago, Pomaderris and Rosaceae where a complete shared target would need
such pooling. In dataset 74913, broad and species labels for Eucalyptus,
Melaleuca, Plantago and Pomaderris are present together in source sample
label records. Co-occurrence is not proof of either exclusivity or overlap;
it only prevents the simpler disjoint-dataset argument used above.

Unresolved broad heath, Proteaceae, Rutaceae, Fabaceae and Podocarpaceae
columns are excluded while separately shared identified bins are retained.
The Myrtaceae/cf./type/slash bins are excluded rather than split or forced
into one family. Identified `Leptospermum` remains comparable in all three
sources. Named bins unavailable in at least one source are also excluded,
rather than kept by inventing a zero column there.

These are different reasons for loss: an unshared named bin is a definite
absence of a common recorded category; unresolved broad/narrow semantics
are an evidence gap that might be resolved. Low retained mass is a possible
consequence of this rule, not a reason to change it after inspecting coverage.

A broader alternative would require either source counting documentation
establishing mutually exclusive residual categories or an **explicitly revised
working assumption** that each archived variable is an additive category
weight, even when it has a nested name. The latter is not protocol evidence
and is not used in these drafts. It would need prospective scientific review
and a recorded change to proposal revision 2 before any distances.

## Dryland convention

Both schemes apply the inherited Lake Selina paper-informed exclusions for
Cyperaceae, Restionaceae, Xyridaceae, Portulacaceae and Ranunculus. The sedge
rule also excludes Baumea, Carex, Eleocharis and Gymnoschoenus; current
Restionaceae placement also excludes Centrolepis. These are declared
denominator conventions, not statements that every member of each family
is aquatic or uninformative about terrestrial vegetation.

The broad modern `Ranunculaceae` bin is excluded as **incomparable**, not
classified wholesale as outside dryland: it cannot be split to remove the
excluded Ranunculus component. The NISP `Anemone` bin is unshared and
incomparable, not declared aquatic merely because it belongs to that family.

## Coarse partition

The coarse mapping pools only already retained primary bins:

| Coarse target | Primary bins pooled |
| --- | --- |
| Proteaceae | Agastachys, Banksia, Bellendena, Orites, Telopea |
| Podocarpaceae | Lagarostrobos, Microcachrys, Pherosphaera, Phyllocladus, Podocarpus |
| Ericaceae | Monotoca, Richea, Sprengelia |
| Cunoniaceae | Bauera, Eucryphia |
| Nothofagus | Nothofagus cunninghamii, Nothofagus gunnii |

Other retained bins keep their primary labels: relabelling a singleton to
its family would add no coarsening. This is a **coarse compatible partition
with family pools**, not a claim that every output bin has exactly the same
taxonomic rank. Family targets here mean the retained identified subset;
they do not reconstruct complete family pollen totals. Previously excluded
broad family columns remain excluded.

The sole additional source bin is modern percentage `Nothofagus`, admitted
to the genus target for the newly eligible datasets. No other exclusion is
reversed. On existing primary-eligible rows, source retention is therefore
unchanged by construction, provided the parent eligibility audit confirms
the excluded genus-only bin is absent there. The parent must check this
before freezing. Changing pool membership and calibration representatives
when new datasets enter remains part of the declared combined sensitivity.

## Evidence keys

Botanical pages were consulted on 13 November 2026. They verify names or
parentage, **not** the archived analysts' grain-counting protocols. No
third-party source prose is reproduced here.

| Key | Evidence and scope |
| --- | --- |
| HEADERS | Line 1 of `../lake-selina/data/counts.tsv`, `../tas-surface/data/percent.tsv`, `../pollen-media/data/counts.tsv`; labels only. |
| BINOMIAL_RULE | Individually declared upward mappings of named species to their own genus; uncertain/composite labels are not parsed as binomials. |
| COMMON_TARGET_RULE | All three source tables must have an explicit, compatible recorded target. Header absence is not repaired with zeros. |
| DRYLAND | `../lake-selina/AMENDMENT-1.md`, paper-informed denominator section; application-6 revision 2 extends the rule to descendants. |
| EXCLUSIVITY_UNRESOLVED | `../lake-selina/INTAKE.md`, residual-category assumption; `../tas-surface/REPORT.md`, archived category/denominator caveats. These do not establish exclusive counting. |
| NISP_LABEL_SCOPE | Saved `../tas-surface/source/neotoma-tas-surface-download.json`, datasets 74305 and 74913, sample `datum[].variablename` memberships. No datum values were used. |
| NOTHOFAGUS_RULE | Application-6 proposal revision 2, species-resolved primary and genus-only dataset eligibility; parent ledger enforces it. |
| PHEROSPHAERA | [UTAS key](https://dicotkey.utas.edu.au/dicotkey/CONIFERS/sPhaerosphaera.htm), [USDA Microstrobos species list](https://npgsweb.ars-grin.gov/gringlobal/taxon/taxonomyspecieslist?id=7613&type=genus): the older genus contains names now assigned to Pherosphaera; genus-only modern identification remains genus-only. |
| LAGAROSTROBOS | [Kew taxon record](https://powo.science.kew.org/taxon/910807-1): Dacrydium franklinii is the species synonym of Lagarostrobos franklinii. |
| BRASSICACEAE | [Royal Botanic Gardens Victoria / NSW flora key](https://keybase.rbg.vic.gov.au/keys/4635): Brassica is included within Brassicaceae. |
| GENTIANACEAE | [Kew family treatment](https://powo.science.kew.org/taxon/urn%3Alsid%3Aipni.org%3Anames%3A30000253-2/general-information): both Gentiana and Gentianella belong to the family. |
| GYROSTEMONACEAE | [USDA family genus list](https://npgsweb.ars-grin.gov/gringlobal/taxon/taxonomygenuslist?id=503&type=family): Didymotheca is assigned to Gyrostemonaceae (as a synonym of Gyrostemon). |
| WINTERACEAE | [Kew Tasmannia record](https://powo.science.kew.org/taxon/urn%3Alsid%3Aipni.org%3Anames%3A555234-1), [USDA Drimys record](https://npgsweb.ars-grin.gov/gringlobal/taxon/taxonomydetail?id=14692), and [generic-separation study](https://doi.org/10.3732/ajb.91.3.321): shared family placement, with generic distinction preserved by upward pooling. |
| CYPERACEAE | [ANU Australasian Pollen and Spore Atlas family index](https://apsa.anu.edu.au/samples/browse.php): Cyperaceae includes Baumea, Carex, Eleocharis and Gymnoschoenus. |
| CENTROLEPIS | [NSW Flora Online genus treatment](https://plantnet.rbgsyd.nsw.gov.au/cgi-bin/NSWfl.pl?lvl=gn&name=Centrolepis&page=nswfl), [Kew genus record](https://powo.science.kew.org/taxon/urn%3Alsid%3Aipni.org%3Anames%3A6717-1): current Restionaceae placement. |
| COARSE_PARTITION | The table above; [ANU index](https://apsa.anu.edu.au/samples/browse.php) verifies the selected Proteaceae and Podocarpaceae genera; [Missouri Botanical Garden APweb](https://www.mobot.org/MOBOT/Research/APweb/genera/cunoniaceaegen.html) includes Bauera and Eucryphia in Cunoniaceae. Current Ericaceae placement is supported by [NSW Monotoca](https://plantnet.rbgsyd.nsw.gov.au/cgi-bin/NSWfl.pl?constat=&dist=&lvl=gn&name=Monotoca&page=nswfl&showsyn=), [Kew Richea](https://powo.science.kew.org/taxon/331910-2) and [University of Sydney Sprengelia](https://eflora.sydney.edu.au/taxon/sprengelia). |

No distances, thresholds, retained-mass ratios, richness estimates or other
analytical outcomes were computed to select these mappings. The parent
will apply the CSVs through study operations and evaluate the intake
consequences before scientific review and freeze.
