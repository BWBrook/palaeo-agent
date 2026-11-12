"""Write the CONISS reference cases: public count tables and the toolkit's coordinates for R (sprint 14).

uv run references/r/coniss/make_cases.py
"""

import json
from pathlib import Path

import numpy as np

from palaeo_agent.coniss import coordinates, zonation

HERE = Path(__file__).resolve().parent


def write_table(name, counts):
    lines = [".\t" + "\t".join(f"t{j + 1}" for j in range(len(counts[0])))]
    lines += [f"s{i + 1}\t" + "\t".join(str(int(v)) for v in row) for i, row in enumerate(counts)]
    (HERE / name).write_text("\n".join(lines) + "\n")


def two_block(seed):
    rng = np.random.default_rng(seed)
    a, b = rng.dirichlet(np.full(8, 2.0)), rng.dirichlet(np.full(8, 2.0))
    return [rng.multinomial(200, a if i < 15 else b).tolist() for i in range(30)]


def dirichlet_like(seed):
    rng = np.random.default_rng(seed)
    base = rng.dirichlet(np.full(12, 1.0))
    return [rng.multinomial(300, rng.dirichlet(40 * base + 0.1 * (i + 1) / 40)).tolist() for i in range(40)]


def profile(counts, transform):
    ids, taxa = [f"s{i + 1}" for i in range(len(counts))], [f"t{j + 1}" for j in range(len(counts[0]))]
    rows = coordinates(counts, transform, ids, taxa)
    record = zonation(counts, transform=transform, sample_ids=ids, taxon_ids=taxa, positions=list(range(len(counts))))
    costs = [m["cost"] for m in record["merges"]]
    inversions = sum(b < a for a, b in zip(costs, costs[1:]))
    flags = [w["code"] for w in record["warnings"] if w["code"].startswith("small_margin")]
    return rows, record, inversions, flags


def main():
    cases = []
    seed = 0
    while True:
        counts = two_block(seed)
        checks = [profile(counts, t) for t in ("relative_abundance", "hellinger")]
        if all(inv and rec["retention"]["later_exceedances"] and not flags for _, rec, inv, flags in checks):
            break
        seed += 1
    write_table("two-block-30x8.dat", counts)
    for transform, (rows, *_rest) in zip(("relative_abundance", "hellinger"), checks):
        cases.append({"id": f"two_block_{transform}", "input": "two-block-30x8.dat", "transform": transform,
                      "seed": seed, "coordinates": rows})
    counts = dirichlet_like(40)
    rows, _, _, flags = profile(counts, "hellinger")
    assert not flags
    write_table("dirichlet-40x12.dat", counts)
    cases.append({"id": "dirichlet_hellinger", "input": "dirichlet-40x12.dat", "transform": "hellinger", "seed": 40,
                  "coordinates": rows})
    counts = [[1, 0], [0, 1], [1, 0]]
    rows, record, _, flags = profile(counts, "relative_abundance")
    assert flags == ["small_margin_merge"] and record["warnings"][-1]["details"]["steps"] == [{"step": 1, "exact_tie": True}]
    write_table("tie-3x2.dat", counts)
    cases.append({"id": "public_tie", "input": "tie-3x2.dat", "transform": "relative_abundance", "seed": None,
                  "coordinates": rows})
    (HERE / "cases.json").write_text(json.dumps({"contract": "docs/sprint-14-contract.md", "cases": cases}, indent=1) + "\n")
    print("two-block seed", cases[0]["seed"], "cases", [c["id"] for c in cases])


if __name__ == "__main__":
    main()
