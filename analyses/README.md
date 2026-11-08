# Analyses

These are worked analyses of real datasets. Each is a standalone script with
pinned dependencies, a `results.json` that the script writes, and a
`report.md` that cites `results.json` by key. To reproduce one:

```bash
uv run analyses/coed-duon-llanvirn/analysis.py
uv run analyses/dielasma/analysis.py
```

Both runs are deterministic: they use fixed seeds and reproduce
`results.json` byte for byte.

| Analysis | Question |
| --- | --- |
| [coed-duon-llanvirn](coed-duon-llanvirn/report.md) | How does Upper Llanvirn shelly-fauna composition change through the Coed Duon section, and which interpretations survive differences in counting totals and in how abundance is represented? |
| [dielasma](dielasma/report.md) | Is *Dielasma* growth isometric, and do three Ford Formation localities differ in shape or size structure? Every result is computed under three treatments of a repeated block in the archived data. |
| [lake-selina](lake-selina/report-final.md) | Where do successive Lake Selina (western Tasmania) pollen spectra differ beyond counting noise, which taxa carry the changes, and how does rarefied pollen-category richness vary? First genuine research application; design frozen in [INTAKE.md](lake-selina/INTAKE.md) before results. |
| [tas-surface](tas-surface/PROPOSAL.md) | Do modern pollen spectra from Tasmanian montane (≥ 700 m) and lowland sites differ in composition, in location rather than dispersion? Second application; waits on proportion input support (sprint 10), because 25 of 27 IPPD surface datasets are archived as percentages. |

**Provenance.**
- Both analyses are corrected versions of the analyst packages from authentic
  sessions A1 and A2, run on 1 November 2026 (Sonnet 5.5, in
  [docs/authentic-sessions-20261101.md](../docs/authentic-sessions-20261101.md)).
- Claude (Opus 5.5) wrote them on 2 November 2026, addressing every finding of
  Codex's (`gpt-6.1-sol`) independent review of the originals.
- A second independent Codex review of these corrected versions
  (`review-codex-20261102.json`) found no major issue. Its minor findings are
  fixed, and each report lists them.
- The [final bounded check](review-codex-final-20261102.md) confirms those
  fixes and byte-identical scratch replays of both scripts. Two final prose
  clarifications are recorded in the [closeout](../docs/recalibration-closeout-20261102.md).
