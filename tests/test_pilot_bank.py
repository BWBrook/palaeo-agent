import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "evaluation/pilot"))
import build_bank  # noqa: E402


def close(a, b):
    if isinstance(a, dict):
        return a.keys() == b.keys() and all(close(a[k], b[k]) for k in a)
    if isinstance(a, list):
        return len(a) == len(b) and all(close(x, y) for x, y in zip(a, b))
    if isinstance(a, float):
        return b == pytest.approx(a, rel=1e-12, abs=1e-15)
    return a == b


@pytest.fixture(scope="module")
def rebuilt(tmp_path_factory):
    root = tmp_path_factory.mktemp("bank")
    build_bank.build(root)
    return root


@pytest.mark.parametrize("part", ["items", "calibration"])
def test_bank_regenerates(rebuilt, part):
    committed = json.loads((ROOT / "evaluation/pilot" / part / "MANIFEST.json").read_text())
    fresh = json.loads((rebuilt / part / "MANIFEST.json").read_text())
    assert committed.keys() == fresh.keys()
    for name in committed:
        if name.endswith("key.json"):
            assert close(json.loads((ROOT / "evaluation/pilot" / part / name).read_text()),
                         json.loads((rebuilt / part / name).read_text())), name
        else:
            assert committed[name] == fresh[name], name


def test_bank_design():
    keys = [json.loads(p.read_text()) for p in sorted((ROOT / "evaluation/pilot/items").glob("*/key.json"))]
    assert len(keys) == 24 and {k["class"] for k in keys} == {"trap", "control"}
    families = {k["family"] for k in keys}
    assert len(families) == 12
    assert sum(k["stratum"] == "toolkit" for k in keys if k["class"] == "trap") == 7
    for k in keys:
        assert k["sufficiency_witness"]
        if k["class"] == "trap":
            assert k["failure_signatures"] and k["issue_tokens"]
    real = {json.loads((p.parent / "provenance.json").read_text())["source"].split(":")[0]
            for p in (ROOT / "evaluation/pilot/items").glob("*-trap/key.json")}
    assert "real" in real
    calibration = {json.loads(p.read_text())["family"] for p in (ROOT / "evaluation/pilot/calibration").glob("*/key.json")}
    assert len(calibration) == 8 and calibration <= families


def test_tasks_do_not_name_the_trap():
    for path in (ROOT / "evaluation/pilot/items").glob("*-trap"):
        task = (path / "materials/task.md").read_text().lower()
        for token in json.loads((path / "key.json").read_text())["issue_tokens"][0]:
            if len(token) > 3 and token not in ("depth",):
                assert token.lower() not in task, (path.name, token)
