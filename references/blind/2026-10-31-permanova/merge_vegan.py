"""Cross-check exact PERMANOVA keys against vegan and attach vegan's betadisper keys."""

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = json.loads((HERE / "fixtures/fixtures.json").read_text())
vegan = json.loads((HERE / "vegan.json").read_text())
report = []
for fx in spec["fixtures"]:
    v = vegan["fixtures"].get(fx["id"])
    if v is None:
        continue
    e = fx["expect"]
    checks = {"F": abs(v["adonis2_F"] - e["F"]) <= 1e-9 * max(1, abs(e["F"])),
              "R2": abs(v["adonis2_R2"] - e["R2"]) <= 1e-9}
    if "adonis2_p_allperms" in v:
        checks["p_allperms"] = abs(v["adonis2_p_allperms"] - e["p_exact"]) <= 1e-12
    report.append((fx["id"], checks, v.get("adonis2_p_allperms"), e.get("p_exact")))
    e["dispersion"] = {"type": "centroid", "bias_adjust": False, "source": f"vegan {vegan['vegan']} betadisper",
                       "distances": v["dispersion_distances"], "group_means": v["dispersion_group_means"],
                       "negative_eigenvalue_count": v["negative_eigenvalue_count"]}
    e["vegan_crosscheck"] = checks
(HERE / "fixtures/fixtures.json").write_text(json.dumps(spec, indent=1) + "\n")
for r in report:
    print(r)
assert all(all(c.values()) for _, c, *_ in report), "vegan disagrees"
