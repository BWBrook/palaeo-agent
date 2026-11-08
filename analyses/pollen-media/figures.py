"""Export the case-study figures and tables from verified API fields in results.json."""

import csv
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


HERE = Path(__file__).resolve().parent
LABELS = {
    "1466027": "H1 core top", "1466028": "H2 moss polster", "1466029": "H3 trap",
    "1480879": "T1 trap", "1480880": "T2 surface", "1480881": "T3 surface", "1480882": "T4 surface",
}


def save(figure, name):
    directory = HERE / "figures"
    directory.mkdir(exist_ok=True)
    figure.savefig(directory / (name + ".png"), dpi=180, bbox_inches="tight")
    figure.savefig(directory / (name + ".pdf"), bbox_inches="tight", metadata={"CreationDate": None})
    plt.close(figure)


def write_tables(result):
    directory = HERE / "tables"
    directory.mkdir(exist_ok=True)
    inclusive = {row["sample_id"]: row for row in result["inclusive_community"]["diversity"]}
    rare = {row["sample_id"]: row for row in result["primary_rarefaction"]["samples"]}
    with (directory / "samples.csv").open("w", newline="") as stream:
        writer = csv.writer(stream, lineterminator="\n")
        writer.writerow(["sample_id", "label", "inclusive_total", "dryland_total", "observed_richness",
                         "rarefaction_size", "expected_richness", "conditional_sd", "estimated_coverage"])
        for row in result["primary_community"]["diversity"]:
            sid = row["sample_id"]
            estimate = rare[sid]["estimates"][0]
            writer.writerow([sid, LABELS[sid], inclusive[sid]["total"], row["total"], row["richness"],
                             estimate["size"], estimate["expected_richness"], estimate["conditional_sd"], estimate["coverage"]])
    with (directory / "pairs.csv").open("w", newline="") as pairs, (directory / "significant-taxa.csv").open("w", newline="") as taxa:
        pair_writer = csv.writer(pairs, lineterminator="\n")
        taxon_writer = csv.writer(taxa, lineterminator="\n")
        pair_writer.writerow(["run", "sample_a", "sample_b", "braycurtis", "p_value", "p_value_holm",
                              "holm_envelope_lower", "holm_envelope_upper", "holm_envelope_unresolved"])
        taxon_writer.writerow(["run", "sample_a", "sample_b", "taxon", "count_a", "count_b",
                               "proportion_difference_b_minus_a", "p_value", "p_value_holm"])
        for name in ("trap_primary", "baseline_tyndall_surface", "trap_inclusive"):
            for pair in result[name]["pairs"]:
                a, b = pair["sample_ids"]
                mc = pair["monte_carlo"]
                pair_writer.writerow([name, a, b, pair["braycurtis_proportions"], pair["p_value"], pair["p_value_holm"],
                                      *mc["holm_envelope"], mc["holm_envelope_unresolved"]])
                for taxon in pair["taxon_tests"]:
                    if taxon["p_value_holm"] <= .05:
                        taxon_writer.writerow([name, a, b, taxon["taxon_id"], *taxon["counts"],
                                               taxon["proportion_difference_b_minus_a"], taxon["p_value"], taxon["p_value_holm"]])


def main():
    result = json.loads((HERE / "results.json").read_text())
    write_tables(result)
    plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False,
                         "pdf.fonttype": 42, "axes.titlelocation": "left"})
    inclusive = {tuple(row["sample_ids"]): row["distance"]
                 for row in result["inclusive_trap_pair_distances"]}
    pairs = result["primary_pair_distances"]
    figure, ax = plt.subplots(figsize=(9.5, 5.5))
    for index, pair in enumerate(pairs):
        key = tuple(pair["sample_ids"])
        primary = pair["distance"]
        color = "#246c62" if key[0].startswith("146") else "#315f9b"
        if key in inclusive:
            ax.plot([primary, inclusive[key]], [index, index], color=color, alpha=.35, lw=2)
            ax.scatter(inclusive[key], index, s=62, facecolors="white", edgecolors=color, zorder=3)
            ax.scatter(primary, index, s=24, color=color, zorder=4)
        else:
            ax.scatter(primary, index, s=35, marker="D", color="#555555", zorder=3)
        ax.annotate(f"{primary:.3f}", (primary, index), xytext=(9, -3), textcoords="offset points", fontsize=9)
    ax.set_yticks(range(len(pairs)), [f"{LABELS[p['sample_ids'][0]]} / {LABELS[p['sample_ids'][1]]}" for p in pairs])
    ax.invert_yaxis()
    ax.set_xlim(0, 1)
    ax.set_xlabel("Relative Bray–Curtis dissimilarity")
    ax.set_title("Collection-media contrasts and the Tyndall surface baseline", pad=16, fontweight="bold")
    for position in (1.5, 4.5):
        ax.axhline(position, color="#dddddd", lw=.8)
    ax.grid(axis="x", alpha=.2)
    ax.set_axisbelow(True)
    ax.scatter([], [], s=30, color="#315f9b", label="Dryland: trap contrast")
    ax.scatter([], [], s=62, facecolors="white", edgecolors="#315f9b", label="Inclusive pollen-sum sensitivity")
    ax.scatter([], [], s=35, marker="D", color="#555555", label="Dryland: surface–surface baseline")
    ax.legend(loc="upper center", bbox_to_anchor=(.45, -.16), ncol=1, frameon=False)
    figure.tight_layout()
    save(figure, "pair-distances")

    primary = result["primary_community"]["diversity"]
    inclusive = {row["sample_id"]: row for row in result["inclusive_community"]["diversity"]}
    rare = {row["sample_id"]: row for row in result["primary_rarefaction"]["samples"]}
    size = result["primary_rarefaction"]["sizes"][0]
    figure, axes = plt.subplots(1, 2, figsize=(10, 5), sharey=True)
    for index, sample in enumerate(primary):
        sid = sample["sample_id"]
        estimate = rare[sid]["estimates"][0]
        color = "#246c62" if sid.startswith("146") else "#315f9b"
        axes[0].plot([sample["total"], inclusive[sid]["total"]], [index, index], color="#aaaaaa", lw=2)
        axes[0].scatter(inclusive[sid]["total"], index, facecolors="white", edgecolors=color, s=45, zorder=3)
        axes[0].scatter(sample["total"], index, color=color, s=20, zorder=4)
        axes[1].plot([estimate["expected_richness"], sample["richness"]], [index, index], color="#cccccc", lw=1)
        axes[1].scatter(sample["richness"], index, facecolors="white", edgecolors=color, s=45, zorder=3)
        axes[1].errorbar(estimate["expected_richness"], index, xerr=estimate["conditional_sd"],
                         fmt="o", markersize=4, color=color, capsize=2, zorder=4)
    axes[0].set_yticks(range(len(primary)), [LABELS[row["sample_id"]] for row in primary])
    axes[0].invert_yaxis()
    axes[0].set_xlim(left=0)
    axes[0].set_xlabel("Counted grains")
    axes[1].set_xlabel("Pollen categories")
    axes[0].set_title("A  Inclusive and dryland totals", fontweight="bold")
    axes[1].set_title(f"B  Observed and rarefied richness (n = {size})", fontweight="bold")
    for ax in axes:
        ax.axhline(2.5, color="#dddddd", lw=.8)
        ax.grid(axis="x", alpha=.2)
        ax.set_axisbelow(True)
    axes[0].scatter([], [], s=45, facecolors="white", edgecolors="#555555", label="Inclusive")
    axes[0].scatter([], [], s=20, color="#555555", label="Dryland")
    axes[1].scatter([], [], s=45, facecolors="white", edgecolors="#555555", label="Observed")
    axes[1].errorbar([], [], xerr=[], fmt="o", markersize=4, color="#555555", capsize=2,
                     label="Expected at common count ±1 conditional SD")
    for ax in axes:
        ax.legend(loc="upper center", bbox_to_anchor=(.5, -.14), frameon=False, fontsize=8)
    figure.tight_layout()
    save(figure, "counts-richness")


if __name__ == "__main__":
    main()
