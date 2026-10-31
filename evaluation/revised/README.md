# Sprint-1 revised evaluation instrument

This is a prospective v2 amendment. The original `evaluation/items`, scorer,
plans and smoke records remain the historical v1 instrument and are never
overwritten.

The builder copies the v1 bank and amends only D2-under and D7-trap. D2 uses
coarser integer percentages without totals to align the catalogue display;
harder uncoached ambiguity construction is deferred to a future pilot bank. D7 explicitly
identifies K5 as failed sampling and requires valid-sample exclusion. Neither
amendment claims to make a harder pilot or establishes efficacy.

The revised scorer inherits v1's numerical tolerances, pair-key symmetry,
pitfall labels/signatures and keyword adjudication, while rejecting malformed
answers and marking numerical answers under an unresolved assumption as
provisional for adjudication. Its evidence check
uses aligned `(path, text)` records, and therefore does not let an unreadable
or oversized file shift the text associated with another output.

From the repository root:

```sh
uv run python -m evaluation.revised.build_items NEW_ITEMS_DIR
uv run python -m evaluation.revised.score RUN_DIR NEW_ITEMS_DIR --output NEW_SCORES.json
```

Both output destinations must be new: the builder and score writer refuse
existing output rather than replacing any historical record. The live trial
launcher is suspended; see [the counter-review](../../docs/sprint-1-review.md).
This module supports offline development checks only.
