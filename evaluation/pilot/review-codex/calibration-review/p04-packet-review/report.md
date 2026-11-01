# P04 blind packet review

Both A and B are acceptable conditional answers. Their campaign means exactly match independent calculations restricted to the >150 µm fraction (T01–T08), and both disclose this restriction and use `completed_with_assumptions`.

| Quantity | Value |
|---|---:|
| 2017 mean, >150 µm | 1.957413573660880 |
| 2021 mean, >150 µm | 1.939520721940205 |
| Common-fraction difference, 2021 − 2017 | -0.017892851720675 |
| 2021 mean, both picked fractions | 2.250092585947499 |

Computed H = −Σ pᵢ ln(pᵢ) separately for each core, then averaged the six core indices in each campaign. No pooling or zero imputation. An algebraically equivalent formula agreed within 6.66e-16. Per-core calculations and all seven input SHA256 hashes are in `verdict.json`.

The task does not specify the intended size fraction. The dictionary establishes a complete common >150 µm fraction, making that conditional target defensible, but does not uniquely select it as the requested target. The 2017 smaller fraction was not picked, so its full-assemblage Shannon mean and a full-assemblage temporal change cannot be recovered. A justified unresolved answer would also be legitimate.

A's phrase “inflate 2021 diversity artificially” is loose: the all-fraction 2021 index is valid, while unequal coverage makes the temporal comparison misleading. Its explicit restriction is adequate, so this is not grounds for rejection. The toolkit capability claim in A cannot be verified from this packet. B gives the clearer account and correctly reports the extra 2021 full-fraction mean rounded to 2.2501.

Only packet materials and A/B were read as evidence; independent calculations were saved before inspecting the responses. No identities, scores, prior adjudications or outside provider calls were used. This review establishes descriptive arithmetic and coverage qualification, not statistical significance or unreported sampling-design comparability.

Verdict SHA256: `c5d7a1942daf5b2c5a909c3996f65fe832d39ed1b3a9a5dada8ff78eb9d1868e`
