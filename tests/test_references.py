import hashlib
import json
from pathlib import Path

import numpy as np
import pytest

from palaeo_agent.community import CommunitySpec, calculate_community


ROOT = Path(__file__).resolve().parents[1]
REFERENCE = json.loads((ROOT / "benchmarks/past/references/community-base-r.json").read_text())


@pytest.mark.parametrize("reference", REFERENCE["cases"], ids=lambda r: f"{r['transform']}-{r['distance']}")
def test_community_matches_base_r_library_reference(reference):
    path = ROOT / REFERENCE["input"]
    data = path.read_bytes()
    assert hashlib.sha256(data).hexdigest() == REFERENCE["input_sha256"]
    spec = CommunitySpec(method="community", input=path, format="past",
                         orientation="taxa_by_samples", value_type="count",
                         transform=reference["transform"], distance=reference["distance"],
                         dimensions=2, missing="error", empty_samples="error")
    result = calculate_community(spec, data)
    assert result["sample_ids"] == reference["sample_ids"]
    assert result["taxon_ids"] == reference["taxon_ids"]
    for actual, expected in zip(result["diversity"], reference["diversity"], strict=True):
        assert actual["sample_id"] == expected["sample_id"]
        for key in ("total", "richness", "shannon", "simpson"):
            assert actual[key] == pytest.approx(expected[key], rel=REFERENCE["rtol"], abs=REFERENCE["atol"])
    for field in ("distances", "eigenvalues", "positive_gram"):
        np.testing.assert_allclose(result[field], reference[field],
                                   rtol=REFERENCE["rtol"], atol=REFERENCE["atol"])
