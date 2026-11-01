# Sprint 5 toolkit review and targeted repairs

Codex, 1 November 2026. Reviewed the toolkit changes introduced by `b9c9a6f`
and present at `799e0de`; no live model calls. The parent authorised the
repairs below after counterexamples were preserved. This delegate changed
only `src/palaeo_agent/community.py`, `src/palaeo_agent/core.py` and
`tests/test_delimited_input.py`, plus this evidence directory.

## Findings repaired

1. **Missing-value conversion changed identifiers.** The new delimited parser
   converted every empty/`NA` cell to `.`, including row and column labels.
   A blank sample or taxon name was therefore accepted as `.`, and a literal
   `NA` identifier was silently renamed. It also stripped whitespace from
   labels despite exact-ID semantics. Missing-value conversion now applies
   only to numeric value cells. Blank IDs are rejected; literal labels,
   including `NA` and surrounding spaces, are preserved. Numeric missing
   tokens are still refused for count analyses.
2. **Malformed delimited records were silently accepted or dropped.** An
   unclosed quote before the final numeric value was accepted by permissive
   CSV parsing; a `,,` record disappeared completely. CSV parsing is now
   strict, with a structured `invalid_delimited` error for malformed quoting.
   Empty physical lines may be ignored, but delimiter-only data records stay
   visible and fail the nonblank-ID check.
3. **Delimited measurement studies could not retain spaced labels.** The
   new study parser correctly read `Shell length` and `Shell width`, then
   wrote them into a derived tab-separated PAST table. The RMA reader still
   split every whitespace character and reported duplicate columns. It now
   uses tab boundaries when the header contains tabs, preserving column and
   sample labels. The old whitespace-only PAST form remains supported.

The pre-fix public-API counterexamples are in `receipt-before.json`, with
`check.py` providing the reproducible examples. `receipt-after.json` shows
that malformed/missing labels now fail, literal identifiers remain intact,
and the spaced-label measurement study completes. No task-specific input
special cases were introduced.

## Follow-up: supported PAST padding contract

The parent's full native suite caught a regression introduced by the initial
RMA tab-preservation repair: frozen blind fixture R17 uses a padded final
header (`Y  `) and surplus trailing tab/space cells. It must retain its
previous numerical result. The fixture was not changed.

RMA now retains literal tab-separated header identities and chooses an exact
requested label first. If an unpadded selector has no exact match, it may
identify one uniquely whitespace-padded PAST label. Ambiguous matches and
x/y selectors resolving to the same column are refused. Such a resolution
emits a saved `padded_column_label` warning containing the selector, actual
raw header and data-column index. Literal padded labels selected explicitly
in a delimited study remain exact. Surplus cells beyond the declared width
are permitted only when every such cell is whitespace; declared values are
not discarded or filled.

The follow-up run passed **57 tests** across the blind fixtures, RMA,
delimited input and study suites, in 16.67 seconds. All 60 objective blind
fixtures pass, and the pre-existing single judgment disagreement remains
explicit. Regression coverage also checks exact padded labels, ambiguous
padding and two selectors resolving to one column.

## Other checks

- Original targeted tests passed **11/11** before repairs: delimited input
  and MCP tests. Their coverage did not expose the three findings above.
- After repairs, **59 tests passed** across delimited input, MCP, RMA and
  study suites (`uv run pytest -q tests/test_delimited_input.py
  tests/test_mcp.py tests/test_rma.py tests/test_study.py`), in 18.43 seconds.
- Added regression cases cover blank sample/taxon labels, delimiter-only
  records, malformed quotes, value-cell missingness, literal `NA` labels,
  preservation of surrounding spaces, and an RMA study that retains spaced
  column/sample IDs and reproduces successfully.
- Equivalent PAST, declared tab and declared comma community results agree;
  declared-delimiter PERMANOVA agrees with its equivalent PAST calculation.
- A quoted-comma taxon name survives a delimited-input study, its derived PAST
  table, integrity inspection and reproduction.
- Advertised MCP schemas contain no unresolved local references. Invalid
  compact `run`/`validate` specifications still receive full typed validation
  errors with the missing field names. Full method schemas remain available
  through discovery, including requirements, limitations and output schemas.
- Capability labels now explicitly expose Shannon and the other implemented
  statistics. Compact schema size is an interface-payload result, not evidence
  of a live token-ratio improvement. Additional discovery calls can offset
  savings; no new K estimate is claimed.

## Integration consequence

The toolkit source corrections require rebuilding the v4 runtime and
refreshing its probes, qualification and fingerprints before any live freeze.
The parent coordinates that rebuild after all review fixes are combined.
This review did not rebuild or alter the existing frozen runtime.
