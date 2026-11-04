# PAST 5.4 individual rarefaction reference

On 5 November 2026, a fresh macOS PAST 5.4 session opened the unchanged
Llanvirn table, selected all ten sample columns and ran Diversity → Individual
rarefaction. Settings were Sample All, Richness S, Conditional uncertainty,
Numbers One-sigma; both plot-for-smallest-N and step-by-one were unchecked.
The numeric table was copied through PAST's Copy action, pasted into a new
TextEdit document, saved as UTF-8 plain text, and read back from disk. The
About panel and numerical/settings panels were captured locally.

`rarefaction-past.json` records the input and raw-export hashes, settings,
comparison scope and all 260 comparisons: ten samples at sizes 1–13, for
expected richness and conditional SD. Every value agrees within the
six-significant-digit export tolerance, 5e-6 relative with a 1e-12 absolute
floor. Maximum absolute difference was 4.9865514964e-6. The toolkit's
conditional SD corresponds to PAST's `Std.err 1s` under this setting; it is
not uncertainty about population richness. Coverage was not compared in PAST.

Screenshots and the full raw export remain local under
`references/past/captures/sprint7-rarefaction/`; the public receipt contains
only generated numerical comparisons. No PAST software, manual or source
text is included. The input can be fetched with `scripts/fetch_past.py`.
The receipt is checked by `tests/test_assemblage_references.py`.

This is a bounded GUI reference check, not a claim of general PAST parity.
