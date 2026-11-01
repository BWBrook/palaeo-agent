You are working on a palaeontological research question, set out in the brief below. Your working directory holds the data and a provenance note. Work only through the `mcp__worker__worker_*` tools:
- `mcp__worker__worker_execute` runs Python 3.12 in the working directory, with numpy, scipy, pandas and matplotlib installed.
- `mcp__worker__worker_read` and `mcp__worker__worker_write` read and write files there.

Leave these deliverables in the working directory:
- `analysis.py`: one runnable script. Run as `python analysis.py` in a directory holding only the original data files and anything you keep under `specs/`, it must recompute every number you report and write `results.json`. Fix the seed of anything random.
- `results.json`: the numbers your conclusions rest on, as `analysis.py` writes them.
- `report.md`: your answer, the evidence for it, the analytical choices you made and why, and what the data cannot establish. Cite values from `results.json`.

Figures are optional.

The Palaeo-Agent toolkit is also installed: as the `mcp__worker__palaeo_*` tools (start with `mcp__worker__palaeo_discover`) and as the Python package `palaeo_agent`. Using it is optional. Use it where it helps you, or not at all.

## Brief

Is shell growth in these Dielasma samples isometric or allometric in length
against width, and do the three localities differ in shell shape or size
structure? Produce a checkable analysis and explain what these samples can
and cannot establish about the populations, their environments and their
taxonomy.
