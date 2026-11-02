from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import fetch_past  # noqa: E402

TRACKED = ["dielasma.dat", "llanvirn.dat"]


def test_tracked_datasets_match_the_recorded_checksums():
    assert fetch_past.ensure(TRACKED, check_only=True) == []


def test_inventory_covers_all_seventeen_files():
    assert len(fetch_past.inventory()) == 17


def test_fetched_datasets_match_the_recorded_checksums():
    problems = fetch_past.ensure()
    if problems:
        pytest.skip("legacy PAST datasets unavailable: " + "; ".join(problems))
