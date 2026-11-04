You are working on a palaeontological research question, set out in the brief below. Your working directory holds the data and a provenance note. Work only through the connected `mcp__worker__*` tools:
- `mcp__worker__worker_execute` runs Python 3.12 in the working directory, with numpy, scipy, pandas and matplotlib installed.
- `mcp__worker__worker_read` and `mcp__worker__worker_write` read and write files there.

Leave these deliverables in the working directory:
- `analysis.py`: one runnable script. Run as `python analysis.py` in a directory holding only the original data files and anything you keep under `specs/`, it must recompute every number you report and write `results.json`. Fix the seed of anything random.
- `results.json`: the numbers your conclusions rest on, as `analysis.py` writes them.
- `report.md`: your answer, the evidence for it, the analytical choices you made and why, and what the data cannot establish. Cite values from `results.json`.

Figures are optional. Save necessary unsupported preparation in `analysis.py`, with provenance. Explain unsupported analytical steps and why they are needed. Keep fresh bundle identifiers and paths in a provenance manifest or the report, outside the numerical `results.json`.
