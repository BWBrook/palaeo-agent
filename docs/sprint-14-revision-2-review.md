# Sprint 14 revision 2: exact model accepted, bounded rounding needed

Codex, 12 November 2026. Review of `d132377`, following Board 3293.
**Accept the exact clustering model, with one required rounding correction
before implementation.** The earlier four numerical findings are addressed.
No scientific-design change or another full contract round is needed.

The common dyadic integer scale, exact cluster sums, rational Ward costs,
exact cumulative SS and strict broken-stick decisions are sound. Constant
coordinates now have zero dispersion exactly; the nearconstant identity no
longer depends on a relative floating-point tolerance. The reference split
is appropriate: an independently written exact centroid/partition-SS oracle
for the method, and pinned rioja for ordinary cases.

## One remaining defect: the starting guess can make the helper stall

The contract seeds square-root rounding with `sqrt(float(q))`, then checks
exact squared midpoint inequalities and walks to an adjacent float if needed.
Those checks establish correctness only after the search reaches the nearby
candidates. They do not establish a practical bound on getting there.

For the permitted abundance input

```text
[[1e300, 1e-300],
 [1e300, 1e300],
 [1e-300, 1e300]]
```

the small exact proportions are about 1e-600. Converting one to float gives
zero, but its correctly rounded square root is **1e-300**, a normal binary64
number. The prototype starts at zero and advances one neighbour at a time.
The review deliberately aborts after 129 `nextafter` calls; reaching the
answer would require roughly 1.2e17 upward steps.

This is not an input that should ultimately be refused. The existing toolkit
abundance validator accepts the source values. Independently rounding by a
bounded binary64-encoding search gives:

```text
[[1, 1e-300],
 [0.7071067811865476, 0.7071067811865476],
 [1e-300, 1]]
```

The exact prototype hierarchy then completes, with costs
`0.2928932188134525` and `0.7642977396044842`, and one retained zone.
All positive coordinates and reported quantities are normal.

There is also a nonzero-subnormal seed failure. For the row `[3, 1e-323]`,
the small proportion rounds to about 5e-324. Its square-root seed is
`2.2227587494850775e-162`, while the correct root is
`1.8148749191817537e-162`. Both are normal, but the neighbour walk is again
far too long. Checking coordinate representability after the walk cannot
protect either case.

## Required correction and acceptance

Use exponent-scaled seeding with a proved local bound, or a bounded search
on binary64 encodings. Retain exact midpoint comparisons and ties to even.
A cap that simply refuses this otherwise valid input would narrow the stated
input domain rather than implement the promised rounding.

The independent review reference bisects the positive encodings in [0,1]
(the full coordinate domain), then rounds from the final adjacent pair by
exact midpoint inequalities. It needs at most **62 bisection steps**.
It is review evidence, not a request to copy this exact implementation.
[Python's binary64 packing specification](https://docs.python.org/3.12/library/struct.html)
supports that encoding model; [`nextafter`](https://docs.python.org/3.12/library/math.html#math.nextafter)
moves a specified number of neighbours, not a relative-distance jump.

Add explicit rounding tests for:
- exact proportions whose floating-point seeds are zero or subnormal,
  but whose roots are normal;
- exact midpoint ties on both even and odd significands;
- the normal/subnormal boundary and the stated `numerical_range` rule.

The promised exact oracle must not inherit coordinate mistakes by blindly
sharing the production rounding helper. Test the coordinates against an
independent rounding reference or verify their exact rounding intervals
separately, then use the independent centroid oracle for the hierarchy.
Keep the accepted mathematical model and application question unchanged.
Incorporate this bounded-rounding correction, then proceed to implementation
with the planned implementation review before application 5 runs.

## Checks performed

- Reran Claude's committed prototype: **all checks passed**.
- A bounded independent rounding review found the seed/search issue.
  The parent independently reproduced both failures with a call guard;
  the prototype was not left running or allowed an unbounded search.
- An independently written partition-SS oracle exactly matched the integer
  prototype's full merge records on **20** small synthetic hierarchies,
  including runner-up costs, boundary order and cumulative dispersion.
- The bounded coordinate reference passed **six** exact midpoint/half-even
  cases. The wide-range input's hierarchy also matched the independent oracle.

The [probe](../references/independent/2026-11-12-sprint14-revision-review/probe.py)
and [receipt](../references/independent/2026-11-12-sprint14-revision-review/receipt.json)
record these artificial checks and source hashes. Run:

```sh
uv run references/independent/2026-11-12-sprint14-revision-review/probe.py
```

These checks establish the observed failures and the tested exact identities;
they do not test a production implementation that has not yet been written.
No full suite, new R reference, cross-platform execution or maximum-size timing
benchmark was run in this review. No engine code or existing numerical result
changed. The complete primer was read (0.2.0.dev0,
`f84855fca5b314f8f608b2ead07d12a94555a93dfe4002195fa537cd2ecf372e`).
CONISS is absent from the catalogue, so the bespoke artificial contract
arithmetic is declared unsupported review work. Lake Selina was not zoned.
