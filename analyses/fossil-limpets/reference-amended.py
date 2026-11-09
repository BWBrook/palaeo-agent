"""Independent arithmetic reference only; scientific estimates remain the API outputs."""

import csv
import hashlib
import json
from pathlib import Path
import subprocess

import numpy as np

HERE = Path(__file__).resolve().parent


def main():
    result = json.loads((HERE / "results-amended.json").read_text())["paired_summary"]
    boot = result["bootstrap"]
    work = HERE / "runs-amended-reference"
    work.mkdir(exist_ok=True)
    index = np.random.Generator(np.random.PCG64(boot["seed"])).integers(
        0, result["n"], size=(boot["replicates"], result["n"]), dtype=np.int64)
    np.savetxt(work / "indices.csv", index + 1, fmt="%d", delimiter=",")
    values = {"difference": result["difference"], "standard_error": boot["standard_error"],
              "interval_low": boot["interval"][0], "interval_high": boot["interval"][1],
              "sign_changes_a": boot["sign_changes"]["a"], "sign_changes_b": boot["sign_changes"]["b"]}
    for prefix, band in zip(("lower", "upper"), boot["endpoint_bands"], strict=True):
        values.update({f"{prefix}_rank_low": band["order_statistics"][0], f"{prefix}_rank_high": band["order_statistics"][1],
                       f"{prefix}_band_low": band["band"][0], f"{prefix}_band_high": band["band"][1]})
    with (work / "summary-api.csv").open("w", newline="") as stream:
        writer = csv.writer(stream, lineterminator="\n")
        writer.writerow(["field", "value"])
        writer.writerows(values.items())
    subprocess.run(["Rscript", "--vanilla", str(HERE / "reference-amended.R"), str(HERE), str(work)], check=True)
    with (work / "receipt.csv").open() as stream:
        receipt = next(csv.DictReader(stream))
    receipt.update(quantities=int(receipt["quantities"]), max_absolute_difference=float(receipt["max_absolute_difference"]),
        absolute_tolerance=1e-10, relative_tolerance=1e-10,
        scope="Base-R inference, all 9999 paired replicate slopes/differences and summary arithmetic; PCG64 indices supplied to match draws; no coverage or scientific validity claim",
        inputs=[{"file": name, "sha256": hashlib.sha256((HERE / name).read_bytes()).hexdigest()}
                for name in ("source/STable1_2DLimpets.csv", "bootstrap-amended.csv", "inference-amended.csv", "results-amended.json")],
        reference_files=[{"file": name, "sha256": hashlib.sha256((HERE / name).read_bytes()).hexdigest()}
                         for name in ("reference-amended.py", "reference-amended.R")])
    (HERE / "r-check-amended.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps(receipt, indent=2))


if __name__ == "__main__":
    main()
