ABUNDANCE_TABLE = ".\tA\tB\tC\nS1\t50.5\t30.25\t19.25\nS2\t10\t60\t30\nS3\t0\t80.5\t19.5\nS4\t25\t25\t50\nS5\t70\t0\t30\nS6\t5.5\t44.5\t50\n"


ABUNDANCE_METADATA = "sample_id,band\nS1,high\nS2,high\nS3,high\nS4,low\nS5,low\nS6,low\n"


ABUNDANCE_COMMUNITY = {"method": "community", "format": "past", "orientation": "samples_by_taxa", "value_type": "abundance",
             "transform": "none", "distance": "braycurtis", "dimensions": 2, "missing": "error", "empty_samples": "error"}


ABUNDANCE_PERMANOVA = {"method": "permanova", "format": "past", "orientation": "samples_by_taxa", "value_type": "abundance",
             "transform": "relative_abundance", "distance": "braycurtis", "missing": "error", "empty_samples": "error",
             "design": "independent", "permutation_scheme": "free", "permutations": 999, "seed": 3,
             "group_column": "band"}


def abundance_table(text, factors=None):
    rows = [line.split("\t") for line in text.strip().split("\n")]
    if factors:
        rows = [rows[0]] + [[r[0], *[repr(float(v) * f) for v in r[1:]]] for r, f in zip(rows[1:], factors)]
    return ("\n".join("\t".join(r) for r in rows) + "\n").encode()
