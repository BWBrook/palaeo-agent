"""Generate review fixtures for an independent R interval comparison."""

import csv
from pathlib import Path

from palaeo_agent.permanova import _monte_carlo_fields


directory = Path(__file__).resolve().parent
cases = [(0, 999), (999, 999), (10, 999), (49, 999), (200, 999),
         (687, 9999), (0, 7), (3, 3), (1, 1), (0, 1)]
with (directory / "cp.csv").open("w", newline="") as stream:
    writer = csv.writer(stream, lineterminator="\n")
    writer.writerow(["b", "B", "lo", "hi", "unresolved"])
    for b, draws in cases:
        fields = _monte_carlo_fields("monte_carlo", b, draws)
        writer.writerow([b, draws, *fields["tail_probability_interval"],
                         int(fields["monte_carlo_unresolved"])])
