# Archived PAST 2001 case studies

Start with [the offline case-study index](html/doc1.html).

This bounded capture contains all 14 original vignettes, the 10 suggested-answer
pages linked from them, the case-study index, and 49 directly referenced images.
The source pages were captured on 30 October 2026. The originals are retained
byte-for-byte in `originals/`; `html/` contains UTF-8 reading copies with source
banners and rewritten links to the local pages, images and datasets. Links to
material outside this capture retain their original online destinations.

The 17 data files from Barry's supplied `../casefiles.ZIP` are extracted without
changes in `../legacy-data/`. The original ZIP remains intact. [The capture
manifest](manifest.json) records the archive, every member, every acquired page
and every image with source information, byte counts and SHA-256 checksums.
[The case inventory](../legacy-cases.json) maps cases to their linked datasets.

Reproduce the extraction and verify/regenerate existing reading copies without
network access from the repository root:

```sh
python3 scripts/capture_past.py --offline
```

To acquire missing sources, omit `--offline`. Existing source checksums are
verified before reuse. `--refresh` explicitly replaces captures with newly
retrieved versions; review the resulting Git diff before accepting an update.

These are the **2001** examples, not an inventory of PAST 5 datasets or numerical
results newly obtained from PAST 5. Historical scientific interpretations and
recommended tests are preserved as source material; they are not automatically
endorsed as current statistical guidance.

The pages, images, manual and example data remain third-party material with
their original attribution. They are retained in this private development
repository at Barry's request for cross-checking. Public accessibility does not
establish an open redistribution licence; no such licence is asserted here.
No PAST executable is included.
