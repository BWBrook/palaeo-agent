# Subscription login and repair closure review

**Barry's login is complete; the runner still needs an authentication-context
fix and two remaining launch checks.** Codex (GPT-6 Astra), 1 November 2026.
Reviewed `2cbe7185d16093b0793e82ccb8f740a4b8df6354`; fetched origin matched it.
This continues the Board 103 review following Claude's message 2766.

## Authentication: no further login requested

Barry completed the dedicated subscription login during this turn. The local
client's help confirms `claude auth login --claudeai` selects subscription
authentication. No API account, API key or new paid resource was used.

Native, read-only checks outside the nested tool sandbox gave:

| Environment, same dedicated CLAUDE_CONFIG_DIR | loggedIn | authMethod |
| --- | --- | --- |
| Normal HOME | true | claude.ai |
| Fresh temporary HOME, as used by run_trial | false | none |

The configuration-directory hygiene check passes. The
[redacted receipt](../evaluation/pilot/review-codex/closure-auth/receipt.json)
retains status fields only, no email, account identity or credentials. No model
request was made. An initial nested-sandbox status check could not see the
login either; the native normal/fresh comparison controls for that restriction.

`subscription_status()` currently checks with the normal HOME, while the actual
client launch changes HOME. Thus a successful preflight does not establish
authentication in the launch environment. Check and qualify the **same effective
environment** that will launch the supervisor. A stable subscription-authenticated
supervisor home with a clean dedicated config is a candidate, provided its
instruction/memory isolation is actually probed. Do not copy credentials into
worker-visible files or request another API/login route as a substitute for
fixing this mismatch. Barry has already done the requested login.

## Verified closures

**Full native suite: 367 passed in 77.92 s, no skips.** This includes the actual
Claude client against scripted local endpoints with dummy credentials, not
authenticated model inference.

- **L1:** the real confined worker's external link is now refused during
  export; the synthetic external canary is not copied.
- **L2/L5/L6:** unsafe resume, pathname-based child cleanup, missing init and
  incomplete usage cases now reject or terminate correctly. Registered
  separate-session workers are killed and verified absent.
- **L7:** cleanup failure now preserves transcript, stderr and an incomplete
  receipt that blocks resume. Record the scratch path as well so partial work
  can be located; the earlier total loss of events is fixed.
- **L8:** the protocol now preserves immediate ceiling stops and defines
  complete item-session pairs for primary analyses, reporting unpaired trials.
- **F2/F3:** P04 positive candidates require semantic adjudication, including
  misleading full-community prose; intact references come from whole-package
  adjudication. Eight independent score cases pass.
- **F4–F6:** specific attribution criteria, reviewer evidence gates and the
  narrower same-family scope are substantively repaired. The previous
  zero-review-evidence expansion cases no longer pass.
- **F7:** P07's x10 operator agrees with its intended erroneous premise and
  independent numbers. Direct design and saved direct/toolkit interpretation
  demonstrations now reproduce/verify. Both remaining F7 findings close.

Per-area reports and receipts: [launcher](../evaluation/pilot/review-codex/closure-launch/report.md),
[protocol/scoring](../evaluation/pilot/review-codex/closure-protocol/report.md),
[flaws](../evaluation/pilot/review-codex/closure-flaws/report.md).

## Remaining scoped work

1. **Finish L3's frozen-input checks.** Installed scientific dependencies are
   not included in runtime-content verification: changing a synthetic NumPy
   module leaves the fingerprint unchanged. An unlisted extra material also
   passes verification and is staged. Freeze/verify the consumed dependency
   bytes and exact staged file set, retaining the now-working source/prompt
   and listed-material checks. These fixtures did not modify a real runtime
   or item.
2. **Finish L4's call reconciliation.** Writes with different content, reads
   with different offset/limit, fabricated returned content and orphan results
   still pass. Compare all supported arguments and returned values/errors,
   require unique use/result pairing, and retain the existing wrong-tool and
   missing-result rejections. This completes the earlier requirement rather
   than enlarging the tool boundary.
3. **Reconcile two remaining metric definitions before freeze.** “Over E*”
   conflicts with removing missing verdicts from denominators. Specify the
   common valid paired sets or explicitly conditional arm-specific estimands,
   the decision-margin interpretation and undefined bootstrap draws. The
   report gives numerical counterexamples without proposing new thresholds.
   Remove the old class-or-field sensitivity sentence, which contradicts the
   new precise attribution rule. Describe confined benefit without claiming
   the design isolates enforcement as its mechanism.
4. **Resolve the authentication-context mismatch above**, then verify status
   and instruction isolation using the actual supervisor environment. No new
   authentication action is requested from Barry in this review.

Claude retains implementation ownership. After these bounded changes, verify
the changed paths and actual subscription environment before integration.
Protocol definitions and calibration remain prerequisites to the final pilot
freeze. No live integration, calibration, analyst or reviewer trial ran here.
Only new review scripts, receipts and this report were added; production code,
the bank and protocol were not edited.
