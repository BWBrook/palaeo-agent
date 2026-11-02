# Corrected authentic derivatives: final bounded check

Read-only review of commit 36813b2646bfb5a11e5b56aef3c765c1677e571b on 2 November 2026. Scope: analyses/README.md, the recorded independent second review, both final scripts/reports/results. Existing independent methodology review was reused; no new broad methods audit was attempted.

## Findings addressed

- Coed Duon taxon inference now uses Holm-adjusted Fisher tests: only Talin among the disputed membership changes is significant (0.0039773); Salop (0.0501011) and Tripl (0.0808214) are explicitly suggestive. Plug-in nondetection probabilities are labelled descriptive, and zero counts are not treated as proof of absence. Basil's 0/26 carries the one-sided 95% upper bound 0.1088304. The 6–7 null percentile is correctly printed as 0.30 (saved 0.3048433).
- Dielasma adds the requested empirical-pairs null bootstrap: each locality is centred, log width is rescaled to the common SMA SD ratio, and paired observations are resampled before recomputing the LR. Independent checks of the source data confirm the imposed SD ratio and preserved correlation for all three localities under all three scenarios. Reported pairs-bootstrap p-values are 0.071, 0.057, 0.046; the report keeps heterogeneity tentative and states the 1,999-replicate Monte Carlo limitation.
- Mixture fitting uses 4 × 4 × 3 = 48 EM starts, retains the best likelihood, and separates component medians from fitted length-density modes. The final L3 two-component BIC is 17.8989981, compared with 13.7756498 for one component, resolving the identified inferior local optimum. This bounded check does not claim proof of a global mixture optimum.
- Histogram edges now span 2 to 26 in steps of two recorded units, with unit-free output keys. Independent reconstruction of all nine locality/scenario histograms reproduces the saved bins/counts, and every histogram sums to its sample size. L3 now includes all 35 specimens, including length 3.5.
- The identified Dielasma rounding corrections are present: L1 p=0.21, block-removed common slope 1.000, archived Gaussian-bootstrap p=0.051, ratio Kruskal–Wallis range 0.031–0.034, and L1–L3 ratio p=0.083. Curvature wording is now “No curvature detected” with an explicit limitation.

## Minor residual wording

Coed Duon's interpretation summary (report.md:156) still says “disappearance of Basil”. In view of the now-correct upper-bound discussion, “decline to zero observed specimens” would be more precise. Salop's displayed p=0.050 (line 114) would be clearer as 0.0501, although the text correctly calls it suggestive and says only Talin is significant. These are small prose clarifications, not computational blockers.

## Verification limits

Replay uses only existing cached Python 3.12.13 with NumPy 2.5.4 and SciPy 1.18.1, matching script pins, with -B to prevent bytecode writes. Scripts and their source data are copied to a temporary mirror retaining the expected analyses/ and benchmarks/ relative paths. No dependency fetch, live inference call, scientific-runtime change, project edit or tracked-result overwrite is performed. Exact results hashes and runtime are recorded below when replay completes. The original independent review remains the basis for methods outside the specifically amended areas.

## Final replay result

**Accept the final derivative corrections, with the two minor prose clarifications above.** Both full scratch executions exit 0 without stderr and reproduce their saved results.json byte for byte.

- coed-duon-llanvirn: SHA-256 `60af441c32e925864fbdc04181e2b5c3221db3a469b2016ac67a2c3011fc493a`; 2.35 seconds.
- dielasma: SHA-256 `f8cd7b4b43d7182ee02c76248891450b68edbe5624495318018d1e7683c73cfa`; 106.5 seconds.

Scratch mirror: `/private/tmp/corrected-derivatives-review-uec75fjc`. Machine-readable replay receipt: `/private/tmp/corrected-derivatives-final-check.json`.

Integration note: final git diff inspection shows the parent has already changed the Coed Duon summary to “decline of Basil to zero observed specimens”. That residual is therefore resolved in the shared working tree. Other dirty paths belong to concurrent parent integration; this delegate made no project edits. Salop's optional precision clarification remains a minor display issue, with the actual inference already correct.

Parent integration: Salop is now printed as p_Holm = 0.0501. Both prose clarifications are resolved; scripts and results are unchanged.
