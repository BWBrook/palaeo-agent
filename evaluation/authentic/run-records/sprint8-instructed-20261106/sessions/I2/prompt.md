You are working on a palaeontological research question, set out in the brief below. Your working directory holds the data and a provenance note. Work only through the connected `mcp__worker__*` tools:
- `mcp__worker__worker_execute` runs Python 3.12 in the working directory, with numpy, scipy, pandas and matplotlib installed.
- `mcp__worker__worker_read` and `mcp__worker__worker_write` read and write files there.

Leave these deliverables in the working directory:
- `analysis.py`: one runnable script. Run as `python analysis.py` in a directory holding only the original data files and anything you keep under `specs/`, it must recompute every number you report and write `results.json`. Fix the seed of anything random.
- `results.json`: the numbers your conclusions rest on, as `analysis.py` writes them.
- `report.md`: your answer, the evidence for it, the analytical choices you made and why, and what the data cannot establish. Cite values from `results.json`.

Figures are optional. Save necessary unsupported preparation in `analysis.py`, with provenance. Explain unsupported analytical steps and why they are needed. Keep fresh bundle identifiers and paths in a provenance manifest or the report, outside the numerical `results.json`.

Use the Palaeo-Agent toolkit for this analysis. Before any analysis, read its full versioned primer through `mcp__worker__worker_execute` by running:

```python
import json
import palaeo_agent
print(json.dumps(palaeo_agent.primer(), ensure_ascii=False))
```

Follow the primer. The toolkit is installed in this Python runtime; scientific MCP tools are withheld. Use the Python API through `mcp__worker__worker_execute`, retaining reproducible calls in `analysis.py`. The printed object includes the full text, version and SHA-256 metadata; a hash alone is not delivery of the primer.

## Brief

Is shell growth in these Dielasma samples isometric or allometric in length
against width, and do the three localities differ in shell shape or size
structure? Produce a checkable analysis and explain what these samples can
and cannot establish about the populations, their environments and their
taxonomy.
