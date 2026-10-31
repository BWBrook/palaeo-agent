# Data dictionary

Tables are tab-separated. The first row holds column labels and its first cell is `.`; the first column holds row labels.

`shells.tsv`: columns `L1/length`, `L1/width`, `L2/length`, `L2/width`, `L3/length`, `L3/width`, in millimetres. Each locality's specimens are listed from the first row downwards independently of the other localities, so a row number does not identify the same specimen across localities. The row labels are row numbers only.

A `.` means no value: either the locality has fewer specimens than the longest column, or the measurement could not be taken because the shell was broken.
