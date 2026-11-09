"""Combine inspected API pairs and fitted fields on shared plotting scales."""

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
from matplotlib import pyplot as plt

HERE = Path(__file__).resolve().parent


def main():
    fits = json.loads((HERE / "results.json").read_text())["fits"]
    fig, axes = plt.subplots(2, 2, figsize=(9, 7), sharex=True, sharey="row", layout="constrained")
    for column, (name, title, x_label, y_label) in enumerate([
            ("caliper_log", "Calipers", "length", "width"),
            ("automorph_log", "AutoMorph", "major axis", "minor axis")]):
        result = fits[name]
        pairs = result["pairs"]
        x, y = [p["x"] for p in pairs], [p["y"] for p in pairs]
        color = ("#27688d", "#b14e36")[column]
        axes[0, column].scatter(x, y, s=19, alpha=0.7, color=color, edgecolor="none")
        endpoints = [min(x), max(x)]
        axes[0, column].plot(endpoints, [result["intercept"] + result["slope"] * v for v in endpoints], color=color)
        axes[0, column].set(title=f"{title}: b = {result['slope']:.3f}, r = {result['correlation']:.3f}",
                            ylabel=f"log$_{{10}}$({y_label} / mm)")
        axes[1, column].scatter(x, [p["residual"] for p in pairs], s=19, alpha=0.7, color=color, edgecolor="none")
        axes[1, column].axhline(0, color="0.4", linewidth=0.8)
        axes[1, column].set(xlabel=f"log$_{{10}}$({x_label} / mm)", ylabel="Vertical residual (log$_{10}$ units)")
        for row in (0, 1):
            axes[row, column].spines[["top", "right"]].set_visible(False)
            axes[row, column].grid(alpha=0.16)
    directory = HERE / "figures"
    directory.mkdir(exist_ok=True)
    fig.savefig(directory / "scaling.png", dpi=180, metadata={"Software": "Matplotlib"})
    fig.savefig(directory / "scaling.pdf", metadata={"CreationDate": None, "ModDate": None})
    plt.close(fig)


if __name__ == "__main__":
    main()
