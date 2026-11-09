"""Artificial, independent checks of the draft inference contract; no fossil data."""

import json
from pathlib import Path
import subprocess

import numpy as np
import scipy
from scipy.stats import binom, f, t

rng = np.random.default_rng(9132026)
n, trials, rho = 20, 2000, 0.05
z = rng.standard_normal((trials, n, 2))
x = z[:, :, 0]
y = rho * x + np.sqrt(1 - rho * rho) * z[:, :, 1]
xc = x - x.mean(axis=1, keepdims=True)
yc = y - y.mean(axis=1, keepdims=True)
sx = np.sqrt((xc * xc).sum(axis=1) / (n - 1))
sy = np.sqrt((yc * yc).sum(axis=1) / (n - 1))
r = (xc * yc).sum(axis=1) / ((n - 1) * sx * sy)
b = np.sign(r) * sy / sx
B = (1 - r * r) * f.ppf(0.95, 1, n - 2) / (n - 2)
hi = np.sqrt(1 + B) + np.sqrt(B)
lo = 1 / hi
end1, end2 = b * lo, b * hi
primary = ((np.minimum(end1, end2) <= 1) & (1 <= np.maximum(end1, end2))).sum()
positive = ((sy / sx * lo <= 1) & (1 <= sy / sx * hi)).sum()

x = np.array([-2., -1., 0., 1., 2.])
y = np.array([-1., -2., 0., 2., 1.])
nulls = []
for beta in (1., -1.):
    r_rf = float(np.corrcoef(y - beta * x, y + beta * x)[0, 1])
    statistic = r_rf * np.sqrt(3) / np.sqrt(1 - r_rf * r_rf)
    nulls.append({"null_slope": beta, "r_rf": r_rf, "t": float(statistic),
                  "p_value": float(2 * t.sf(abs(statistic), 3))})

confidence = np.nextafter(1., 0.)
edge = 0.75 * f.ppf(confidence, 1, 1)
direct = np.sqrt(1 + edge) - np.sqrt(edge)
rational = 1 / (np.sqrt(1 + edge) + np.sqrt(edge))
reference = subprocess.run(["Rscript", "--vanilla", "-e",
                            "cat(sprintf('%.17g',log(2)+pt(100,1000,lower.tail=FALSE,log.p=TRUE)),R.version.string,sep='\\n')"],
                           check=True, capture_output=True, text=True)
reference_tail, r_version = reference.stdout.splitlines()
degenerate_probability = (135 / 136)**136 + (1 / 136)**136
receipt = {
    "scope": "Independent artificial contract review; no toolkit implementation or application-4 inference",
    "numpy_version": np.__version__, "scipy_version": scipy.__version__, "r_version": r_version,
    "normal_simulation": {"generator": "default_rng(9132026); standard_normal((2000,20,2)); constructed y=rho*x+sqrt(1-rho**2)*z2",
                          "n": n, "trials": trials, "rho": rho, "true_signed_slope": 1,
                          "sample_sign_reversals": int((r < 0).sum()),
                          "sample_sign_primary_coverage": float(primary / trials),
                          "prior_positive_component_coverage": float(positive / trials),
                          "binomial_99_9_percent_band": (binom.ppf([0.0005, 0.9995], trials, 0.95) / trials).tolist()},
    "opposite_null_signs": nulls,
    "interval_cancellation": {"n": 3, "r": 0.5, "confidence": float(confidence),
                              "subtractive_lower_factor": float(direct), "rationalized_lower_factor": float(rational)},
    "tail_underflow": {"t": 100, "df": 1000, "scipy_sf": float(t.sf(100, 1000)),
                       "scipy_logsf": str(t.logsf(100, 1000)),
                       "base_r_two_sided_log_p": float(reference_tail)},
    "rounded_bootstrap_fixture": {"rows": 136, "identical_rows": 135,
                                   "probability_all_resampled_rows_identical": degenerate_probability},
}
path = Path(__file__).with_name("receipt.json")
path.write_text(json.dumps(receipt, indent=2, allow_nan=False) + "\n")
print(json.dumps(receipt, indent=2, allow_nan=False))
