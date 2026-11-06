# Dielasma shell measurements: provenance

**Source.** Measurements of the Permian terebratulide brachiopod *Dielasma*
from the Zechstein reef facies of the Ford Formation, Sunderland area, NE
England (populations studied by Hollingworth & Pettigrew 1988). The file is
the copy distributed with the PAST case studies (Hammer, Harper & Ryan 2001,
*Palaeontologia Electronica* 4(1)), case study 1.

**Samples.** Three discrete samples, one from each of three localities in the
reef complex (L1, L2, L3). The genus often forms monospecific clusters,
presumed to be in-place living assemblages.

**Measurements.**
- Taken with vernier calipers on the pedicle valve of conjoined (articulated)
  shells.
- `X1` is sagittal length; `X2` is maximum width.
- Units are not stated in the archived source.

**File `dielasma.dat`.**
- Whitespace-separated. The first row names the columns: `L1/X1`, `L1/X2`,
  `L2/X1`, `L2/X2`, `L3/X1` and `L3/X2`. The `.` at its start is a placeholder
  for the corner cell.
- Each further row begins with a row number, then the six values. One row
  holds one specimen per locality: the X1 and X2 columns of a locality belong
  to the same specimen, but specimens in the same row at different localities
  are unrelated.
- `.` marks no specimen. The samples hold 103 (L1), 79 (L2) and 35 (L3)
  specimens.

**Not recorded.** Collecting method, the stratigraphic or ecological position
of each locality within the reef, and specimen ages.
