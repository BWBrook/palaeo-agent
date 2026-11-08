# Neotoma reader repair confirmation

Codex (`gpt-6.1-sol`), 8 November 2026. Reviewed `7642a7b`.
No production code, tests or demonstration outputs were changed by this review.

**All six original findings are closed. One small numeric-validation
regression needs a focused repair.**

## P2: null/object percentage values leak TypeError

At `src/palaeo_agent/neotoma.py:113`, `_value` calls `Decimal(value)` before
checking that the value is a supported numeric type. A percentage datum
with `value: null` or `value: {}` raises raw `TypeError`. The exception
handler at line 117 does not catch that type. The earlier implementation
returned `invalid_abundance` for such nonnumeric values.

Check the type before conversion, or translate `TypeError` into the existing
structured `invalid_abundance` refusal. Cover null, object and list values;
the list case already returns the correct refusal. No new error category or
framework is needed. This does not affect the supplied examples.
The other acceptance criteria are met; this calls for the targeted guard and
reader/MCP regressions, not another broad audit.

## Confirmed repairs

- **MCP schema:** live stdio discovery now advertises `NeotomaSpec` through
  its actual definition. A correct request satisfies that schema and runs;
  the schema and server both refuse the extra scientific `method` field.
- **Numeric fidelity:** underflow, overflow and the oversized percentage
  integer give `invalid_abundance`. A positive 1e-300 is preserved; ordinary
  derived-file bytes are unchanged. The NISP cap is covered by the suite.
- **Labels:** control characters give `unsupported_label`; literal quotes
  remain in `taxa.csv` and the analytical result's `taxon_ids`.
- **Datum fields:** the original wrong-type cases give `invalid_source`.
- **Manifests:** list, boolean version and external-symlink cases all give
  `invalid_bundle`.
- **Lockfile:** fresh bundles contain and hash `uv.lock` when the environment
  declares it captured. Inspection enforces the presence/provenance match.
- **Depth ordering:** the additional infinite-depth case gives `depth_order`.

The original 20 input probes and live transport/bundle probes were rerun in
new scratch directories. Full suite: **787 passed, 11 skipped**, including
the new live advertised-schema test; optional native confinement tests were
not enabled.

Fresh copied demonstrations regenerate surface `percent.tsv`, `samples.csv`,
`study.json` and `results.json` byte for byte. Selina's `extract-check.json`
is also byte-identical: the 72 × 66 table matches its frozen counts, and all
144 age rows retain the recorded 72 defaults and level/bound comparisons.
The parent checked transport, bundles, suite and demonstrations; the bounded
independent check confirmed the input repairs and identified the regression.

The primer remains **0.2.0.dev0**, SHA-256
`bea68f9f65925dcbe4aeeeb2ccb7b74a0915ac4c8ce856e1b49b2e038271d5ac`.
Its full text was read in the preceding review and its unchanged metadata
verified here. Supported operations used the API. Adversarial source
construction, source-shape checking and byte comparisons are review tasks;
these checks make no new ecological claim.

Evidence is in
[`confirmation-7642a7b.json`](../references/independent/2026-11-08-neotoma-reader/confirmation-7642a7b.json).
The original reproducer scripts are unchanged. Reproduce the remaining issue
from the repository root with a new scratch directory:

```bash
uv run references/independent/2026-11-08-neotoma-reader/probe_percent_types.py /tmp/neotoma-percent-types
```
