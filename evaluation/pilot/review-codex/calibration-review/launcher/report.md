# Remaining launcher closure review

Reviewed `4a80b5f`, including repair commit `b69fd10` and integration changes
in `172c96e`, on 1 November 2026. **The reported L3/L4 residual defects are
closed by the current implementation.** The subscription-status environment
mismatch is also corrected in source; its saved qualification evidence is
qualified below.

The independent [check script](check.py) produced **22/22 passing checks**;
[receipt.json](receipt.json) pins the reviewed files and observations. All
fixtures were synthetic. No global user instructions, memory, credentials,
authenticated client or provider were accessed. The status subprocess was
mocked. The parent owns the full native suite and review of actual trials.

## L3: consumed runtime and material contents

- `fingerprints()` now hashes the full runtime tree and the base interpreter
  tree, including regular-file bytes and symlink targets. Changing a synthetic
  installed numerical dependency or the synthetic base interpreter changes
  the fingerprint. This closes the earlier `numpy`-mutation counterexample.
- `verify_materials()` now compares the exact item's file set with its
  manifest, checks hashes and rejects links/special entries. It returns the
  verified material list, and `stage()` consumes that list. An additional
  unlisted material, a changed task and a material symlink are each rejected.
- The earlier source/prompt pinning and no-follow export remain in place.
  Scratch paths are now recorded at allocation in both started and trial
  records, and failed workspaces are retained rather than deleted.

## L4: complete reconciliation

- Write contents and read offsets/limits are now part of the matched request.
  Defaults are normalised explicitly, and the default-read positive control
  passes.
- Each worker result must match the exact value the trusted adapter returns,
  including the error flag. Toolkit JSON decoding/wrapping is represented by
  `adapter_value()` rather than comparing the wrong raw wrapper.
- Changed write content, changed read range and fabricated execution/toolkit
  returned values are rejected. Valid execution and toolkit results pass.
- Duplicate use IDs, duplicate results and orphan results are rejected.

These checks close the concrete counterexamples in
`review-codex/closure-launch/`. No consequential residual was found in this
bounded review of the changed L3/L4 paths. This is not a claim of exhaustive
security verification.

## Subscription environment and saved qualification

`subscription_status(home, config_dir)` now uses the same cwd, HOME and
`environment(home, config_dir)` builder as the live supervisor launch. The
synthetic subprocess check confirms that equality. Source inspection shows a
fresh HOME whose only added access is the login-keychain link; instruction
ancestor checks and disabled automatic memory remain in the launch path.
Neither that keychain path nor any authentication command was opened or run
in this review.

The saved `supervisor-qualification.json` records:

- one request each for clean capture, positive control and supervisor;
- a detected planted instruction canary and instruction preamble in the
  positive control;
- no instruction preamble, memory section or selected user markers in the
  clean capture/supervisor requests;
- a logged-in `claude.ai` team subscription in the tested supervisor HOME;
- dummy API-key headers and no Authorization header to the local fake
  endpoint; zero inference calls.

The qualification script's current SHA-256 matches its receipt. Its launcher
and three prompt fingerprints, however, precede the `172c96e` changes. The
reviewed diff adds gating/recording of organisation-managed settings and
corrects tool-name spelling in prompts; it does not change the supervisor
HOME, launch authentication environment or instruction-disabling flags.
Thus this is relevant source-bound evidence for the repaired authentication
path, not a newly reproduced current-tree qualification. The underlying
request bodies were deliberately not retained, so their negative scan results
cannot be independently rerun from this receipt alone.

The new managed-settings gate accepts empty settings plus recognised policy
fields, records the policy and checks again after the trial. Synthetic empty
settings pass and nonempty managed settings are rejected. Before freezing a
revised bank/launcher, refresh and pin the qualification against that final
source/prompt version. Do not describe the older receipt as matching a newer
commit merely because its verdict is positive.

No actual-model trial authorisation, calibration validity or inference about
toolkit benefit follows from this launcher-only review.
