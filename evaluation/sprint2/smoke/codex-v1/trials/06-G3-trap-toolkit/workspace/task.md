# Community group comparison

Assess the facies-associated difference in community composition using a one-way
PERMANOVA with Bray-Curtis dissimilarity on the untransformed specimen counts.
Use freely exchangeable independent sampling units only when the sampling
description supports that design. Do not aggregate samples or substitute a
different experimental design. Use seed 20261031 and 999 requested permutations;
enumerate all distinct allocations preserving group sizes when feasible.

Report these numerical fields in `results`: `n`, `pseudo_f`, `r_squared`,
`p_value`, `ss_total`, `ss_within`, `ss_between`, `df_between`, `df_within`, and
`group_mean_centroid_distance` (an object with `reef` and `lagoon` means).
The centroid distances are descriptive, without bias adjustment or distance
correction; no dispersion significance test is requested.

Use `answer.json` with the supplied answer contract. Explain the design
assumptions, limitations and handling of identified data problems. If the
requested design is unsupported, set `status` to `stopped`, leave `results`
empty, and identify the sampling units and unsupported design in `issues`.
Preserve your analysis code or specification and enough provenance to rerun it.
Do not launch other agents, agent CLIs or child agent sessions.

A draft interpretation says: "The facies differ in centroid location, and differences in within-facies spread cannot explain the significant PERMANOVA result."

Assess that exact claim. Also report `claim_supported` as 1 if the evidence supports the full claim, otherwise 0, and explain your judgment in `summary`.
