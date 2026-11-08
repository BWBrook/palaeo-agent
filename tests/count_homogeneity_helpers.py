PAIR_TABLE = ".\tA\tB\tC\tD\nS1\t30\t5\t2\t0\nS2\t28\t9\t1\t3\nS3\t10\t20\t5\t1\nS4\t12\t18\t6\t2\nS5\t25\t6\t3\t0\n"


PAIR_BASE = {"method": "count_homogeneity", "format": "past", "orientation": "samples_by_taxa", "value_type": "count",
        "missing": "error", "empty_samples": "error", "simulations": 999, "seed": 3}


def pair_spec(tmp_path, **changes):
    (tmp_path / "t.dat").write_text(PAIR_TABLE)
    return dict(PAIR_BASE, input=str(tmp_path / "t.dat"), **changes)
