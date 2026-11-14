# Application 6 metadata seed

Codex, 13 November 2026; calibration policy amended 14 November under revision
2.1 (`f0a33a6`, Board 3382). The seed implements the metadata portion of
revision 2 (`a351379`, Board 3349). This is a pre-distance draft, not the final eligibility
or representative selection. Only metadata, source-bin labels and their
presence were audited; no distance, cutoff, harmonised composition, diversity
or analogue outcome was computed.

## Source and scope

`metadata-seed.csv` contains exactly **68 unique sample IDs from 27 datasets
and 27 actual collection-unit IDs**. The saved source is
`../tas-surface/source/neotoma-tas-surface-download.json`, SHA-256
`0205169197c51e03da06e914d157136c965cd7bffb13f103817888ff2fb58c36`.
It has 61 percent rows and seven NISP rows. Hartz Mountains (74305) and
Tyndall Ranges (74913) contribute the seven NISP rows; source units are
preserved, not converted.

All source records identify a `Modern` collection unit, a `pollen surface
sample` dataset and a `surface sample` analysis unit. These archival labels
support modern-reference eligibility; they do not prove a collection's
integration period or that a core top has no older material.

The source's `depth` is retained as `original_sample_code`, not interpreted
as sediment depth. Vale of Belvoir's codes include 81, 82 and 83. Each
dataset has a distinct collection-unit ID in this source. No units are
merged because of coincident coordinates.

Evidence keys identify records by dataset, collection-unit and sample/code,
rather than copying source prose or personal contact fields. For example,
`dataset:74304/collectionunit:55664/notes/sample-code:3` locates the note
supporting Harlequin Hill's core-top override. `.../all_samples/datum/
positive_Nothofagus_bins` denotes a dataset-wide audit of its recorded bins.

## Medium is separate from depositional environment

`archived_depositional_environment` copies the source label. `medium`,
`medium_source` and `medium_evidence_key` distinguish three evidence levels:

- Sample-specific collection notes override the collection-unit label.
  Harlequin Hill 1466026 is a core top, although the unit says Moss Polster.
  Its other two samples are moss polsters. Hartz's codes 1/2/3 are core top,
  moss polster and pollen trap. Tyndall's code 1 is a pollen trap; codes 2–4
  are surface samples whose more specific collection media are not stated.
- Mount Anne's notes define the collection as a moss-polster transect.
- For other units labelled Moss Polster, that classification is retained
  explicitly at collection-unit level and flagged as such. A label of
  Swamp, Marsh, Natural Lake or Coastal lagoon describes an environment;
  it does not establish a collection device or material. Those rows remain
  `surface sample (medium unspecified)` unless the notes supply more.

The ledger has 50 moss-polster classifications: seven supported by the
notes above and 43 inherited explicitly from the unit classification.
There are two core tops, two traps and 14 surface samples with unspecified
specific medium. These distinctions are metadata provenance, not a reason
to exclude a medium from this application.

## Altitude and location

Only **13 rows** have documented sample-specific altitudes. The other
**55 sample-altitude and source fields are blank**. Site altitudes remain
in their own columns and are never silently substituted.

| Dataset | Source sample codes and documented altitudes (m) |
| --- | --- |
| 74701, Mount Read | 1: 800; 2: 960 |
| 74644, Mount Anne | 1: 400; 2: 500; 4: 750; 7: 600 |
| 74780, Piney Creek | 1: 172; 2: 167; 3: 174; 4: 170; 5: 165; 6: 172; 7: 163 |

Coordinates are copied only from each archived site-level Point, with no
centroid, sample offset or extra precision invented. All collection-unit
GPS fields are empty. Thus no individual sample's exact location is
established here, even when its altitude is documented.

Two pairs of distinct units share a site Point:

| Datasets | Collection-unit IDs | Rows flagged |
| --- | --- | ---: |
| 74160 Cradle Link Road / 74914 Vale of Belvoir | 55534 / 56140 | 13 |
| 74303 Hardwood River Valley / 74304 Harlequin Hill | 55663 / 55664 | 4 |

All 17 affected rows carry shared-coordinate flags and the other dataset's
ID/site. Equal archived coordinates do not establish identical collection
locations, and do not change the 27-unit grouping. Moxon Saddle Lagoon's
archived Coastal lagoon label alongside a site altitude of 760 m is retained
and flagged as unverified, not silently corrected.

## Dataset-level Nothofagus resolution and eligibility

Resolution is assessed across every sample in a dataset, not separately
from each row's positive taxa. The only recorded positive bins are
`Nothofagus`, `Nothofagus cunninghamii` and `Nothofagus gunnii`. No dataset
mixes the undifferentiated bin with either species bin.

- **`species_recorded`: 19 datasets, 59 rows.** At least one species bin
  is recorded somewhere in the dataset. This demonstrates use of a species
  bin, not a guarantee that an unrecorded species was identifiable in every
  sample. Both count datasets, Hartz 74305 and Tyndall 74913, record both
  named species and no undifferentiated Nothofagus.
- **`genus_only`: six datasets, seven rows.** Datasets 75430, 74779, 74795,
  74777, 75423 and 75421 are excluded as whole datasets from primary
  taxonomic eligibility, exactly as proposal revision 2 specifies. They
  remain taxonomically eligible for the coarse crosswalk.
- **`uninformative`: two datasets, two rows.** Naracoopa 74764/unit 56022/
  sample 1477443 and Lake Flannigan 74569/unit 55863/sample 1472789 record
  no Nothofagus. An all-zero record cannot demonstrate species resolution.
  They remain provisionally eligible under the fixed six-dataset exclusion
  rule, with that uncertainty explicit; no new exclusion was invented.

Before the retained-weight rule is applied, primary taxonomic eligibility
is therefore **61 rows in 21 units**, and coarse taxonomic eligibility is
**68 rows in 27 units**. These are not final candidate counts. The parent
intake must combine these flags with the declared crosswalk, retained-weight
floor and any explicitly reviewed source-quality decision. Unknown altitude
or collection medium does not automatically exclude a row.

## Unresolved denominator at Naracoopa

The earlier [Tasmanian surface report](../tas-surface/REPORT.md) records
retained percentage weights summing to **242.5 at Naracoopa**, for unresolved
reasons. This is an existing reported quantity, not recalculated here.
Sample 1477443 carries a source-quality flag in `unresolved_metadata`.
No corrected units are inferred. Revision 2.1 adds an explicit calibration-only
screen: a native-percent row whose exact extracted land-plant weight before
any exclusions exceeds 100.5 cannot be a representative. It remains a
candidate if the ordinary taxonomy and fixed 0.80 floor rules allow it.
NISP rows are exempt from this percentage screen. Equality to 100.5 passes
this particular rule, without proving a consistent denominator. The final
ledger carries the calculated flag for every affected row, not just the
previously noted Naracoopa example.

Consequently, a retained-weight fraction is not automatically a demonstrated
fraction of counted pollen grains. Explicit row closure can define a
compositional working input without proving a shared source denominator.
This source-quality issue is separate from the fixed retained-weight
coverage floor. The earlier report's sums concern its own pollen sum, not
the new crosswalk's retained weight.

## Representative preference, not selection

`representative_preference` ranks rows **within actual collection-unit ID**:
sample code 1 first, then ascending numeric original sample code, then
numeric sample ID to break a tie. The ledger is ordered by collection-unit
ID and preference. Each unit currently belongs to just one dataset.

The parent intake chooses the first calibration-eligible row separately under
the primary and coarse taxonomy, fixed 0.80 retained-weight, and percentage
screening rules. A unit can have candidates but no eligible representative;
the final ledger and receipt distinguish those cases. No representative,
threshold or nearest neighbour is selected by this seed. If sample 1 fails
eligibility, the next preference can qualify without an outcome-driven
choice. Coincident site Points remain visible without being silently
collapsed into one calibration unit.

The complete versioned primer was read before this work: 0.2.0.dev0,
SHA-256 `fcc02a57db1ffa2a86d14e7c2540bd7bfa89c14e7e5b3334286f9a24b16747f6`.
