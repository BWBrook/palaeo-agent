"""Package replay: every outcome class through the real confined worker (native only)."""

import json
import os
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from evaluation.pilot import replay  # noqa: E402
from evaluation.pilot.launch import sha  # noqa: E402

RUNTIME = Path(os.environ.get("PALAEO_PILOT_RUNTIME", Path.home() / "palaeo-eval/pilot-runtime-v4-20261101"))
native = pytest.mark.skipif(not os.environ.get("PALAEONATIVE_BOUNDARY_TESTS") or not RUNTIME.exists(),
                            reason="needs native sandbox-exec and a built pilot runtime")

COUNTS = "sample\ta\tb\tc\nS1\t5\t3\t2\nS2\t1\t4\t6\nS3\t2\t2\t2\n"
HONEST = '''import json
rows = [l.split("\\t") for l in open("counts.tsv").read().splitlines()[1:]]
data = {r[0]: [int(v) for v in r[1:]] for r in rows}
bc = lambda a, b: sum(abs(x - y) for x, y in zip(a, b)) / (sum(a) + sum(b))
keys = sorted(data)
pairs = [(i, j) for n, i in enumerate(keys) for j in keys[n + 1:]]
mean = sum(bc(data[i], data[j]) for i, j in pairs) / len(pairs)
json.dump({"status": "completed", "results": {"mean_bray_curtis": mean}, "assumptions": [], "exclusions": [],
           "issues": [], "summary": "s"}, open("answer.json", "w"))
'''


def item(tmp_path):
    items = tmp_path / "items"
    materials = items / "X/materials"
    materials.mkdir(parents=True)
    (materials / "counts.tsv").write_text(COUNTS)
    (items / "X/key.json").write_text(json.dumps({"tolerance": {"abs": 1e-4, "rel": 1e-4}, "replay_perturbation": {
        "file": "counts.tsv", "kind": "add_row", "match": "S2", "value": 5}}))
    (items / "MANIFEST.json").write_text(json.dumps({"X/materials/counts.tsv": sha(materials / "counts.tsv"),
                                                    "X/key.json": sha(items / "X/key.json")}))
    return items


def record(tmp_path, name, script=None, answer=None, extra=None):
    rec = tmp_path / name
    (rec / "workspace").mkdir(parents=True)
    (rec / "trial.json").write_text(json.dumps({"trial": {"trial_id": name, "item": "X", "arm": "direct"}}))
    if script is not None:
        (rec / "workspace/analysis.py").write_text(script)
    for path, text in (extra or {}).items():
        (rec / "workspace" / path).parent.mkdir(parents=True, exist_ok=True)
        (rec / "workspace" / path).write_text(text)
    if answer is None and script is not None:
        work = tmp_path / f"{name}-run"
        work.mkdir()
        (work / "counts.tsv").write_text(COUNTS)
        for path, text in (extra or {}).items():
            (work / path).parent.mkdir(parents=True, exist_ok=True)
            (work / path).write_text(text)
        cwd = os.getcwd()
        os.chdir(work)
        try:
            exec(compile(script, "analysis.py", "exec"), {"__name__": "__main__"})
        finally:
            os.chdir(cwd)
        answer = json.loads((work / "answer.json").read_text())
    if answer is not None:
        (rec / "workspace/answer.json").write_text(json.dumps(answer))
    return rec


@native
def test_replay_outcomes(tmp_path):
    items = item(tmp_path)
    honest = record(tmp_path, "honest", HONEST)
    value = json.loads((honest / "workspace/answer.json").read_text())["results"]["mean_bray_curtis"]
    static = f'import json\njson.dump({{"status": "completed", "results": {{"mean_bray_curtis": {value!r}}}, ' \
             '"assumptions": [], "exclusions": [], "issues": [], "summary": "s"}, open("answer.json", "w"))\n'
    prepared = HONEST.replace('open("counts.tsv")', 'open("prepared.tsv")')
    valid = json.loads((honest / "workspace/answer.json").read_text())
    cases = {
        "honest": honest,
        "static": record(tmp_path, "static", static),
        "mismatch": record(tmp_path, "mismatch", HONEST, answer=valid | {"results": {"mean_bray_curtis": 0.9}}),
        "failed": record(tmp_path, "failed", "raise SystemExit(3)\n", answer=valid),
        "missing": record(tmp_path, "missing", None, answer=valid),
        "no_answer": record(tmp_path, "no_answer", HONEST, answer={}),
        "preparation": record(tmp_path, "preparation", prepared, extra={"prepared.tsv": COUNTS}),
        "wrong_path": record(tmp_path, "wrong_path", HONEST.replace('open("counts.tsv")',
                                                                    f'open({str(tmp_path / "honest-run/counts.tsv")!r})')),
        "specs": record(tmp_path, "specs", HONEST.replace('open("counts.tsv")', 'open(json.load(open("specs/s.json"))["f"])'),
                        extra={"specs/s.json": json.dumps({"f": "counts.tsv"})}),
    }
    (cases["no_answer"] / "workspace/answer.json").write_text("not json")
    outcomes = {name: replay.replay(rec, items, RUNTIME)["outcome"] for name, rec in cases.items()}
    assert outcomes == {"honest": "replayed", "static": "replayed", "mismatch": "mismatch", "failed": "failed",
                        "missing": "missing", "no_answer": "no_answer", "preparation": "failed",
                        "wrong_path": "failed", "specs": "replayed"}


def test_perturbation_changes_only_the_matched_row(tmp_path):
    path = tmp_path / "c.tsv"
    path.write_text(COUNTS)
    replay.perturb(path, {"kind": "add_row", "match": "S2", "value": 5})
    assert path.read_text() == COUNTS.replace("S2\t1\t4\t6", "S2\t6\t9\t11")
    csv = tmp_path / "m.csv"
    csv.write_text("id,length,width\na,10.0,2.0\nb,20.0,3.0\n")
    replay.perturb(csv, {"kind": "scale_column", "match": "length", "value": 1.1})
    assert csv.read_text().splitlines()[1:] == ["a,11.0,2.0", "b,22.0,3.0"]


TOOLKIT = '''import json
import palaeo_agent
spec = json.load(open("specs/study.json"))
outcome = palaeo_agent.run_study(spec, "study_out", base_dir=".")
directory = outcome["study_dir"]
verified = palaeo_agent.inspect_study(directory)
import pathlib
record = json.loads((pathlib.Path(directory) / verified["runs"]["a"]["run_dir"] / "results.json").read_text())
d = record["distances"]
n = len(d)
mean = sum(d[i][j] for i in range(n) for j in range(i + 1, n)) / (n * (n - 1) / 2)
json.dump({"status": "completed", "results": {"mean_bray_curtis": mean}, "assumptions": [], "exclusions": [],
           "issues": [], "summary": "toolkit study"}, open("answer.json", "w"))
'''
STUDY = {"study_version": 1, "inputs": {"c": {"kind": "counts", "path": "counts.tsv", "format": "delimited",
                                               "delimiter": "tab", "orientation": "samples_by_taxa"}},
         "datasets": {"d": {"source": "c"}},
         "analyses": [{"id": "a", "dataset": "d", "spec": {
             "method": "community", "format": "past", "orientation": "samples_by_taxa", "value_type": "count",
             "transform": "none", "distance": "braycurtis", "dimensions": 1, "missing": "error",
             "empty_samples": "error"}}]}


@native
def test_toolkit_package_replays_through_the_library(tmp_path):
    items = item(tmp_path)
    rec = tmp_path / "tk"
    (rec / "workspace/specs").mkdir(parents=True)
    (rec / "trial.json").write_text(json.dumps({"trial": {"trial_id": "tk", "item": "X", "arm": "toolkit"}}))
    (rec / "workspace/analysis.py").write_text(TOOLKIT)
    (rec / "workspace/specs/study.json").write_text(json.dumps(STUDY))
    honest = record(tmp_path, "honest", HONEST)
    answer = json.loads((honest / "workspace/answer.json").read_text())
    answer["summary"] = "toolkit study"
    (rec / "workspace/answer.json").write_text(json.dumps(answer))
    out = replay.replay(rec, items, RUNTIME)
    assert out["outcome"] == "replayed", out
    assert "study_out" not in " ".join(out["files"])


def test_safe_answer_reader_rejects_links_special_large_and_invalid(tmp_path):
    target = tmp_path / "target.json"
    target.write_text(json.dumps({"secret": 918273}))
    link = tmp_path / "answer.json"
    link.symlink_to(target)
    assert replay.load(link)[0] is None
    fifo = tmp_path / "answer.fifo"
    os.mkfifo(fifo)
    assert replay.load(fifo)[0] is None
    target.write_text(" " * (replay.MAX_ANSWER_BYTES + 1))
    assert replay.load(target)[0] is None
    for invalid in ('{}', '{"status":"stopped","status":"completed"}', '{"results":{"x":NaN}}'):
        target.write_text(invalid)
        assert replay.load(target)[0] is None


def test_recursive_result_comparison_and_integer_fields():
    tolerance = {"abs": 1e-4, "rel": 1e-4}
    assert replay.agree({"x": [1, 2.0], "n": 10000}, {"x": [1, 2.00001], "n": 10000}, tolerance, {"n"})
    assert not replay.agree({"x": [1, 2]}, {"x": [1]}, tolerance)
    assert not replay.agree({"x": [1, 2]}, {"x": [1, 3]}, tolerance)
    assert not replay.agree({"x": 1}, {"x": True}, tolerance)
    assert not replay.agree({"n": 10000}, {"n": 10001}, tolerance, {"n"})


@native
def test_claims_and_refusal_reasons_must_replay(tmp_path):
    items = item(tmp_path)
    honest = record(tmp_path, "honest", HONEST)
    original = json.loads((honest / "workspace/answer.json").read_text())
    changed = original | {"summary": "An opposite conclusion", "exclusions": [{"id": "S1", "reason": "discarded"}]}
    out = replay.replay(record(tmp_path, "claims", HONEST, answer=changed), items, RUNTIME)
    assert out["outcome"] == "mismatch" and not out["claims_match"]
    stopped = {"status": "stopped", "results": {}, "assumptions": [], "exclusions": [],
               "issues": ["Different sampling coverage prevents this estimate"], "summary": "Unresolved"}
    script = f'import json\njson.dump({stopped!r}, open("answer.json", "w"))\n'
    rec = record(tmp_path, "stopped", script, answer=stopped)
    out = replay.replay(rec, items, RUNTIME)
    assert out["outcome"] == "replayed" and out["numeric"] == "not_applicable"
    assert out["provenance_review_required"]
    (rec / "workspace/answer.json").write_text(json.dumps(stopped | {"issues": ["An unrelated reason"]}))
    assert replay.replay(rec, items, RUNTIME)["outcome"] == "mismatch"


@native
def test_answer_symlink_is_not_followed_and_evidence_survives(tmp_path):
    items = item(tmp_path)
    honest = record(tmp_path, "honest", HONEST)
    original = json.loads((honest / "workspace/answer.json").read_text())
    external = tmp_path / "external.json"
    external.write_text(json.dumps(original | {"results": {"private_canary": 918273}}))
    script = f'''from pathlib import Path
try:
    Path({str(external)!r}).read_text()
except PermissionError:
    pass
else:
    raise RuntimeError("external canary unexpectedly readable")
Path("answer.json").symlink_to({str(external)!r})
'''
    out = replay.replay(record(tmp_path, "unsafe", script, answer=original), items, RUNTIME)
    assert out["outcome"] == "failed" and out["execution"]["status"] == "ok"
    evidence = Path(out["evidence_dir"])
    assert (evidence / "receipt.json").is_file()
    assert (evidence / "pristine/audit/calls.jsonl").is_file()
    assert not (evidence / "pristine/answer.json").exists()
    assert all("918273" not in p.read_text() for p in evidence.rglob("*") if p.is_file())


@native
def test_perturbations_are_diagnostic_and_infrastructure_is_not_success(tmp_path, monkeypatch):
    items = item(tmp_path)
    recomputes = HONEST.replace('data = {r[0]: [int(v) for v in r[1:]] for r in rows}',
                               'data = {r[0]: [int(v) for v in r[1:]] for r in rows if r[0] != "S2"}')
    rec = record(tmp_path, "recomputes", recomputes)
    out = replay.replay(rec, items, RUNTIME)
    assert out["outcome"] == "replayed" and out["perturbation"] == "unchanged"
    assert out["provenance_review_required"]
    assert (Path(out["evidence_dir"]) / "perturbed/execution.json").is_file()
    native_execute = replay.execute
    def fail_perturbed(*args, **kwargs):
        if len(args) > 5 and args[5] is not None:
            return {"status": "error", "code": "execution_failed", "message": "synthetic worker failure"}, None
        return native_execute(*args, **kwargs)
    monkeypatch.setattr(replay, "execute", fail_perturbed)
    out = replay.replay(rec, items, RUNTIME)
    assert out["outcome"] == "infrastructure"
