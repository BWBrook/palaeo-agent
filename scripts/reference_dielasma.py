"""Independent stdlib numerical reference; never imports palaeo_agent or NumPy."""

import hashlib
import json
import math
from pathlib import Path
import statistics
import zipfile


def calculate(archive: Path) -> dict:
    with zipfile.ZipFile(archive) as bundle:
        raw = bundle.read("dielasma.dat")
    rows = [line.split() for line in raw.decode("ascii").splitlines() if line.strip()]
    headers, observations = rows[0], rows[1:]
    cases = []
    for locality in ("L1", "L2", "L3"):
        xi, yi = headers.index(f"{locality}/X1"), headers.index(f"{locality}/X2")
        used = [row for row in observations if row[xi] != "." and row[yi] != "."]
        excluded = [row[0] for row in observations if row[xi] == "." or row[yi] == "."]
        for transform in ("none", "log10"):
            x = [float(row[xi]) for row in used]
            y = [float(row[yi]) for row in used]
            if transform == "log10":
                x, y = list(map(math.log10, x)), list(map(math.log10, y))
            mx, my = statistics.mean(x), statistics.mean(y)
            sx, sy = statistics.stdev(x), statistics.stdev(y)
            correlation = statistics.correlation(x, y)
            slope = math.copysign(sy / sx, correlation)
            cases.append({
                "locality": locality,
                "transform": transform,
                "x": headers[xi],
                "y": headers[yi],
                "missing": "drop_pairs",
                "n": len(used),
                "retained_ids": [row[0] for row in used],
                "excluded_ids": excluded,
                "mean_x": mx,
                "mean_y": my,
                "sd_x": sx,
                "sd_y": sy,
                "correlation": correlation,
                "slope": slope,
                "intercept": my - slope * mx,
            })
    return {
        "reference_kind": "independent_stdlib_calculation_not_PAST_execution",
        "procedure": "scripts/reference_dielasma.py",
        "input_sha256": hashlib.sha256(raw).hexdigest(),
        "rtol": 1e-12,
        "atol": 1e-12,
        "published_raw_slopes": {"L1": 0.84, "L2": 0.82, "L3": 0.91},
        "published_raw_slope_atol": 0.005,
        "cases": cases,
    }


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[1]
    print(json.dumps(calculate(root / "benchmarks/past/casefiles.ZIP"), indent=2, allow_nan=False))
