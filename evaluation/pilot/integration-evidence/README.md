# Integration trials, 1 November 2026

These are the first live trials: Claude Sonnet 5.5 through the subscription
supervisor, on calibration items P05-cal and P10-cal, both arms. They are
development integration tests, not pilot data. Each trial had 10 minutes, 60
turns and no retries.

| Run | Trial | Item | Arm | Outcome | Counted tokens | Notes |
| --- | --- | --- | --- | --- | ---: | --- |
| 20261101 | T001 | P05-cal | toolkit | correct | 28,813 | Complete. Then the halt below. |
| 20261101b | T002 | P05-cal | direct | correct | 7,236 | Ran fully and reconciled. The post-trial check flagged new signature sidecars. |
| 20261101c | T001 | P10-cal | toolkit | correct | 9,288 | Complete. |
| 20261101c | T002 | P10-cal | direct | correct | 3,547 | Complete. |

**Halts, both at the configuration hygiene gate:**

- The first halt came when the client's subscription login fetched the
  organisation's signed managed files: `remote-settings.json` (empty, `{}`),
  `policy-limits.json` (product switches only) and their signature and stamp
  files.
- The second halt was a further sidecar, `*.signature-iat.json`.
- The gate now accepts these files under conditions:
  - managed settings must be exactly `{}`;
  - policy limits may hold only the known fields, and their digest is
    recorded;
  - sidecars of those two files are allowed;
  - the folder is checked again after every trial.

**Integration criteria**
([integration-check.json](integration-check.json), complete trials only):

- successful numerical execution;
- structured toolkit refusals (`invalid_past_header`, `row_width`,
  `duplicate_id`, `unsupported_schema`);
- reproduction of every saved study bundle (3 of 3, re-verified and rerun
  outside the trial).

**Boundary observations**

- Every worker call reconciled with the audit on its full request and the
  exact returned value.
- In each toolkit trial the model called the bare name `worker_read` 3 times.
  The client refused it each time before dispatch.
- That cause was the prompt naming tools without the client's `mcp__worker__`
  prefix. It cost turns in one arm only. The prompts now give the exact names,
  before calibration.

**Toolkit usability finding, not changed before calibration.** On P05-cal the
agent first passed a tab-delimited table as PAST input. It then converted the
file itself and recovered.
