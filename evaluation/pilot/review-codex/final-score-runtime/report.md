# Pilot-v3 scoring and installed-runtime verification

Reviewed `aedc158`, 1 November 2026. The [check script](check.py) and
[receipt](receipt.json) preserve eight scoring cases and runtime provenance.
No live model calls or production edits occurred.

**F1 is closed for the reported evidence-credit defect.** All-left exclusions,
all-right exclusions and averaging now receive identical evidence scores.
Excluding both members of a pair is flagged. This check establishes parity of
valid representations, not scientific correctness of arbitrary saved prose.

**F2 is improved but not closed.** A silent P04 basis is now `undisclosed` and
provisional; a legitimate coverage stop is `correct_unresolved` and provisional.
Explicit common-fraction disclosure is accepted. However the following answer
with the keyed restricted-fraction numbers is also accepted, with
`adjudication_required=false`:

> All fractions were counted in both campaigns; these are full-community Shannon means.

The substring `fraction` satisfies the disclosure token rule even though the
sentence denies the very restriction that must be disclosed. Keyword candidate
positives need semantic adjudication too. The new whole-package adjudication
only covers session-1 controls and therefore does not fix P04 trap/calibration
scoring. Apply a frozen adjudication procedure to these provisional scores
before using them for calibration or pilot endpoints; a full prose parser is
not required.

**Runtime and bank provenance verified.** The on-disk runtime manifest matches
the committed one. Wheel SHA-256 is
`9693a5d6a74996560d25284cadc3c562c2f34a976abb4993c731cf621ee2d936`.
All 11 toolkit Python modules in the wheel, installed runtime and current source
agree byte for byte. All 144 material files across 32 pilot/calibration items,
their numerical targets and existing error signatures are unchanged from
`1d017e9`; those accepted independent calculations still apply.

The earlier independent S1–S4 script was also run through the **installed
toolkit interpreter with `-I`**, rather than the checkout environment:
**29/29 passed**, including partial-study reproduction and malformed manifests
and paths. The separate [installed-study receipt](installed-study-receipt.json)
pins that unchanged script and records the outcomes.

This verifies this MacBook runtime's study code and the recorded wheel. It does
not make the launcher's currently unenforced plan fingerprints effective or
qualify another host.
