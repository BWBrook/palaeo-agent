# Sprint 7: assemblage methods and primer delivery

5 November 2026. Implementation and verification by Codex, with independent
Codex methods review. Claude owns the next scientific code review against the
contracts and the cross-check of the corrected analyses. No live analyst
session was launched in this sprint.

## Delivered

Two operations now work through the Python API, CLI, MCP, saved-run bundles
and prepared studies:

- `rarefaction`: exact individual-count interpolation, expected richness,
  conditional variance/SD, and estimated abundance coverage at the requested
  sizes and the full sample. Sample sizes are explicit or resolve to the
  minimum retained total. No extrapolation or equal-coverage standardisation.
- `count_homogeneity`: declared sample pairs using full counts, fixed-margin
  Pearson Monte Carlo tests, proportional Bray–Curtis, two-sided Fisher
  taxon tests, separate omnibus and global pair-by-taxon Holm families,
  signed taxon effects, and pointwise upper limits for zero counts. The
  counting model does not represent between-collection variation or
  ecological cause.

Both use the shared count parser, declared orientation, metadata alignment
and diagnostics. Ordination-specific sample and matrix limits remain in the
ordination path. Row totals are checked with exact integer sums before float
conversion. The new methods save tables, results, settings, inputs and
provenance; no plot layer was added. Examples are
[`rarefaction-llanvirn.json`](../examples/rarefaction-llanvirn.json) and
[`count-homogeneity-llanvirn.json`](../examples/count-homogeneity-llanvirn.json).

The canonical [primer](../src/palaeo_agent/primer.md) ships inside the package.
Python, CLI and MCP expose identical UTF-8 text with package version and
SHA-256 metadata. Every discovery shape points to it. The MCP server supplies
a compact instruction preface, and the confined worker forwards its exact
content. README and repository instruction files point to the same source;
the earlier draft is a historical pointer, not a second maintained copy.

The authentic-session harness has explicit `mcp` and `python` delivery modes.
Both use the installed toolkit runtime; Python mode withholds scientific MCP
tools and their instructions. New instructed prompts print the whole primer
object, and session fingerprints, tool inventories and replay retain the
delivery mode. Historical A1/A2 prompts, records and frozen runtimes were not
changed.

## Contract corrections and computational limits

The final review corrected the interpretation of rarefied coverage: it
estimates population abundance coverage at that sample size, not the fraction
of the finite observed count mass represented. The implementation replaces
unstable subtraction of large log-gamma values with cached coefficient-ratio
products in 50-digit Decimal arithmetic. Explicit operation limits are
200,000 product factors, 100,000 covariance pair terms and 100,000 requested
sample-size estimates. Unsupported workloads refuse rather than approximate.
Accepted count values and sample totals remain bounded by 2^53−1.

The homogeneity sampler fixes Patefield, PCG64, pair-specific spawned streams,
chunk size 256, the inclusive tail tolerance and all package versions. Pooled
pair totals are capped at 3,037,000,499 to keep the inspected sampler's
signed-int64 products safe, and estimated temporary chunks are capped at
64 MiB. These are implementation bounds, not statistical thresholds.
`simulations` is required in 999–99,999 and `seed` in 0–2^32−1. Settings are
not silently coerced. The signed taxon effect is b minus a; swapping a pair
need not reproduce the same finite Monte Carlo draw.

`monte_carlo_unresolved` means only that the pointwise raw-tail interval
contains the fixed reporting alpha 0.05. A false flag does not certify a
Holm-adjusted decision. The two Holm families do not jointly control one
family-wise error rate over every claim. Zero-count bounds are pointwise;
underflow rounds upward to the smallest positive float.

## Numerical evidence

| Check | Evidence and scope |
| --- | --- |
| Exact small cases | Enumeration of subsamples, exact rational coverage, deterministic boundaries, large-count precision regression, and weighted fixed-margin table enumeration |
| R rarefaction | `vegan::rarefy` 2.7.6, expectation and variance, Llanvirn and boundary fixtures |
| Coverage | Unmodified pinned iNEXT `Chat.Ind` function, executed from upstream source; not an installed-package test |
| R homogeneity | Pearson statistics, Fisher p-values, both Holm families, binomial intervals and zero limits; independent Monte Carlo draws assessed with declared simulation tolerance |
| PAST 5.4 | Fresh GUI export: all 260 expectation/conditional-SD comparisons for ten samples at sizes 1–13 agree within six-significant-digit export tolerance; maximum absolute difference 4.9865514964e-6 |
| Integration | Deleted-source fresh-process reproduction, metadata/table readback, rewritten-checksum consistency failures, prepared-study replay, CLI and real stdio MCP |

The R receipt regenerates byte-identically. See the
[R reference record](../benchmarks/past/references/assemblages-r.md),
[PAST capture record](../benchmarks/past/references/rarefaction-past.md) and
corresponding JSON receipts. PAST coverage was not tested. R's raw tiny
boundary residuals are preserved and judged on the variance scale; the API
returns exact zero at deterministic boundaries. No special Fisher tolerance
exception was needed for these references.

Independent methods review accepted the corrected formulas and implementation
without a calculation or inference blocker. It explicitly checked the
inspection boundary: an in-range but false nondegenerate rarefaction estimate
can pass structural result validation if the saved records are consistently
altered. `inspect` checks hashes and specified consistency invariants;
`reproduce` recomputes numbers. Neither certifies scientific interpretation,
input authenticity, or a correct sampling design.

## Client and installed-package evidence

The qualification uses a fresh installed runtime and a fake local provider;
no request is sent to a model. The scripted sequence obtains the complete
primer before a valid analytical call. This proves delivery for that sequence,
not that an unscripted agent will choose to read or obey it.

The normal full-client launcher route passes all three tested configurations:
direct Python, toolkit MCP and toolkit Python. The six-case matrix additionally
tests `--bare`: five cases pass all checks, but bare toolkit/MCP suppresses
canonical server instructions. Its primer tool still returns the complete
body. Do not claim bare-mode native instruction delivery. The planned I1/I2
route is the full client, not `--bare`.

Claude Code 2.1.311 places the canonical preface inside a system-role message
in the provider `messages` array in the full route. The probe therefore checks
actual preface content rather than one JSON field or a character count. It
excludes tool-result bodies from instruction evidence. Python mode verifies
that scientific MCP instructions are withheld.

The same client introduced a plugin-store bookkeeping file. A session-local
`CLAUDE_CODE_AGENTS_MD_ROWS_EVERY_PROCESS=1` prevents those telemetry-store
reads/writes in the isolated launch environment; the ban on configured plugins
is unchanged. The fresh probe configurations contain no plugins path. This
control is qualified against the recorded client bytes, not assumed for a
future client version. No global settings were changed.

The compact [delivery receipt](../evaluation/sprint7/delivery-qualification.json)
records the wheel, client and source fingerprints, installed-primer checks,
case matrix and native checks. Raw provider records and application screenshots
remain local. This runtime is a qualification artifact, not the sprint-8 freeze.

The installed wheel's API and CLI reproduce the exact primer bytes and
metadata outside the checkout. `uvx --offline --python 3.12.13 --from <wheel>
palaeo-agent primer` also matches the complete header and body. The initial
unpinned offline attempt lacked cached dependencies; the qualified route pins
the project's interpreter and the same wheel artifact.

## Verification commands and handoff

```sh
uv sync --locked --extra mcp
uv run pytest -q
uv run palaeo-agent validate examples/rarefaction-llanvirn.json
uv run palaeo-agent validate examples/count-homogeneity-llanvirn.json
```

Native confinement and termination checks additionally require the documented
macOS execution environment, `PALAEONATIVE_BOUNDARY_TESTS=1`, and
`PALAEO_PILOT_RUNTIME` pointing to the newly built qualification runtime.
The native harness subset passed 61 tests. The installed-package checks and
client matrix are recorded separately from ordinary Python test results.
The final complete local run, with native checks enabled against the fresh
runtime, passed **683 tests in 125.83 seconds** with no skips or failures.
Linux CI on implementation commit `ab28a7a58fff4a683f853bea70b33baf512c7a52`
passed **672 tests, 11 skipped**, in 148.89 seconds; the skipped native
checks were exercised locally. [CI record](https://github.com/BWBrook/palaeo-agent/actions/runs/41932960550).

Claude is next: review the code against the two contracts, then cross-check
the corrected Llanvirn and Dielasma analyses with matched inputs, estimands,
transformations and numerical conventions. The existing multinomial
Bray–Curtis analysis and the new conditional Pearson test have different
null procedures and statistics; disagreement is not automatically a defect.
Compare simulated rarefaction means against exact expectations using the
Monte Carlo error of the mean, not the subsample SD.

After that review, Claude owns the sprint-8 runtime freeze, final qualification,
I1/I2 sessions and synthesis. Preserve the two cases as descriptive evidence;
their difference cannot identify a causal bootstrap effect. No expanded method
catalogue, public `check_values` helper, new scoring bank, additional trial,
release or publication was included here.
