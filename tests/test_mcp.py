import asyncio
import json
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

mcp = pytest.importorskip("mcp")
from mcp import Client, StdioServerParameters

from palaeo_agent.mcp_server import SERVER_INSTRUCTIONS, Transport, create_server, tool_definitions
from palaeo_agent.methods import calculate_method, parse_spec, read_inputs, summary
from palaeo_agent.primer import primer, primer_metadata
from palaeo_agent.runs import inspect_run, run

REPO = Path(__file__).resolve().parents[1]


@pytest.fixture
def materials(tmp_path):
    specs = {}
    for method, source in (("rma", "dielasma-l2"), ("community", "community-llanvirn-raw"),
                           ("permanova", "permanova-llanvirn"),
                           ("rarefaction", "rarefaction-llanvirn"),
                           ("count_homogeneity", "count-homogeneity-llanvirn")):
        spec_path = REPO / "examples" / f"{source}.json"
        spec = json.loads(spec_path.read_text())
        for key in ("input", "metadata"):
            if spec.get(key):
                target = f"{method}-{key}.dat" if key == "input" else f"{method}-{key}.csv"
                shutil.copyfile((spec_path.parent / spec[key]).resolve(), tmp_path / target)
                spec[key] = target
        specs[method] = spec
    return tmp_path, specs


def client(root):
    return Client(StdioServerParameters(command=sys.executable,
                  args=["-m", "palaeo_agent.mcp_server", "--root", str(root)]))


def unpack(result):
    assert result.structured_content is not None
    assert json.loads(result.content[0].text) == result.structured_content
    return result.structured_content


def test_stdio_rma_inference_and_paired_bootstrap(tmp_path):
    from test_rma_paired import table, spec
    path = table(tmp_path)
    paired = spec(path)
    paired["input"] = path.name
    paired["bootstrap"]["confidence"] = 0.999
    single = {"method": "rma", "input": path.name, "format": "past", "x": "L", "y": "W",
              "transform": "log10", "missing": "error", "inference": {"confidence": 0.95, "null_magnitude": 1}}

    async def scenario():
        async with client(tmp_path) as session:
            for request in (single, paired):
                schema = unpack(await session.call_tool("discover", {"method": request["method"]}))
                expected_spec = parse_spec(request | {"input": str(path)})
                expected = calculate_method(expected_spec, read_inputs(expected_spec))
                record = unpack(await session.call_tool("run", {"spec": request}))
                saved = inspect_run(tmp_path / record["run_dir"])["result"]
                assert saved == expected
                assert schema["output_schema"]["properties"]["method_version"]["const"] == saved["method_version"]
                verified = unpack(await session.call_tool("inspect", {"bundle": record["run_dir"]}))
                assert verified["status"] == "verified"
                async with client(tmp_path) as fresh:
                    replay = unpack(await fresh.call_tool("reproduce", {"bundle": record["run_dir"]}))
                    assert replay["status"] == "reproduced" and replay["differences"] == []
    asyncio.run(scenario())


def test_stdio_equivalence_and_fresh_reproduction(materials):
    root, specs = materials

    async def scenario():
        async with client(root) as session:
            tools = await session.list_tools()
            assert {tool.name for tool in tools.tools} == set(item["name"] for item in tool_definitions())
            discovery = unpack(await session.call_tool("discover", {}))
            assert [m["id"] for m in discovery["method_index"]] == [
                "rma", "rma_paired", "community", "permanova", "rarefaction", "count_homogeneity", "coniss"]
            for method, spec in specs.items():
                schema = unpack(await session.call_tool("discover", {"method": method}))
                assert schema["input_schema"]["properties"]["method"]["const"] == method
                py_spec = parse_spec({**spec, "input": str(root / spec["input"]),
                                     **({"metadata": str(root / spec["metadata"])} if "metadata" in spec else {})})
                expected = summary(calculate_method(py_spec, read_inputs(py_spec)))
                valid = unpack(await session.call_tool("validate", {"spec": spec}))
                assert valid["status"] == "valid"
                record = unpack(await session.call_tool("run", {"spec": spec}))
                assert record["summary"] == expected
                assert not Path(record["run_dir"]).is_absolute()
                inspection = unpack(await session.call_tool("inspect", {"bundle": record["run_dir"]}))
                assert inspection["summary"] == expected
                assert "result" not in inspection
                assert all((root / entry["path"]).is_file() for entry in inspection["artifacts"])
                spec_path = root / f"{method}.json"
                spec_path.write_text(json.dumps(spec))
                command = subprocess.run([sys.executable, "-m", "palaeo_agent", "run", str(spec_path),
                                          "--output", str(root / "cli")], capture_output=True, text=True, check=True)
                assert json.loads(command.stdout)["summary"] == expected
                async with client(root) as fresh:
                    repeated = unpack(await fresh.call_tool("reproduce", {"bundle": record["run_dir"]}))
                    assert repeated["status"] == "reproduced"
                    assert repeated["differences"] == []
    asyncio.run(scenario())


def test_stdio_refusals_and_root_boundaries(materials, tmp_path):
    root, specs = materials
    outside = root.parent / f"{root.name}-outside"
    outside.mkdir()
    (outside / "matrix.dat").write_text("secret canary")
    (root / "escape").symlink_to(outside, target_is_directory=True)

    async def scenario():
        async with client(root) as session:
            cases = [
                ("run", {"spec": {**specs["rma"], "input": str(outside / "matrix.dat")}}, "path_outside_root"),
                ("run", {"spec": {**specs["rma"], "input": "escape/matrix.dat"}}, "path_outside_root"),
                ("run", {"spec": specs["rma"], "output": "escape/new"}, "path_outside_root"),
                ("inspect", {"bundle": "../"}, "path_outside_root"),
                ("reproduce", {"bundle": "escape"}, "path_outside_root"),
                ("inspect_comparison", {"bundle": "escape"}, "path_outside_root"),
                ("compare", {"baseline": "escape", "sensitivity": "runs"}, "path_outside_root"),
                ("validate", {"spec": {**specs["permanova"], "design": "repeated"}}, "invalid_request"),
                ("run", {"spec": {}}, "invalid_request"),
                ("discover", {"unexpected": True}, "invalid_request"),
                ("result", {"bundle": "runs", "field": "distances", "limit": 101}, "invalid_request"),
                ("not_a_tool", {}, "unknown_tool"),
            ]
            for name, args, code in cases:
                result = await session.call_tool(name, args)
                assert result.is_error, (name, args, result)
                record = unpack(result)
                assert record["code"] == code
                assert "secret canary" not in json.dumps(record)
        assert not (outside / "new").exists()
    asyncio.run(scenario())


def test_comparison_and_pagination(materials):
    root, specs = materials

    async def scenario():
        async with client(root) as session:
            baseline = unpack(await session.call_tool("run", {"spec": specs["community"]}))
            changed = unpack(await session.call_tool("run", {"spec": {**specs["community"], "transform": "relative_abundance"}}))
            comparison = unpack(await session.call_tool("compare", {"baseline": baseline["run_dir"],
                                                                     "sensitivity": changed["run_dir"]}))
            assert comparison["status"] == "complete"
            inspection = unpack(await session.call_tool("inspect_comparison", {"bundle": comparison["comparison_dir"]}))
            assert inspection["status"] == "verified"
            assert inspection["summary"] == comparison["summary"]
            result = json.loads((root / baseline["run_dir"] / "results.json").read_text())
            page = unpack(await session.call_tool("result", {"bundle": baseline["run_dir"], "field": "distances",
                                                               "offset": 1, "limit": 2, "column_offset": 2,
                                                               "column_limit": 3}))
            assert page["total"] == len(result["distances"])
            assert page["value"] == [row[2:5] for row in result["distances"][1:3]]
    asyncio.run(scenario())


def test_interrupted_bundle_is_never_complete(materials, monkeypatch):
    root, specs = materials

    def interrupted(*args):
        raise KeyboardInterrupt("simulated process interruption before manifest")

    monkeypatch.setattr("palaeo_agent.runs._plot", interrupted)
    with pytest.raises(KeyboardInterrupt):
        run({**specs["rma"], "input": str(root / specs["rma"]["input"])}, root / "partial")
    partial, = (root / "partial").iterdir()
    assert not (partial / "manifest.json").exists()

    async def scenario():
        async with client(root) as session:
            result = await session.call_tool("inspect", {"bundle": str(partial)})
            assert result.is_error
            assert unpack(result)["code"] == "invalid_bundle"
    asyncio.run(scenario())


def test_single_call_interface(materials):
    root, specs = materials
    result = subprocess.run([sys.executable, "-m", "palaeo_agent.mcp_server", "--root", str(root),
                             "--call", "validate"], input=json.dumps({"spec": specs["rma"]}),
                            capture_output=True, text=True, check=True)
    assert json.loads(result.stdout)["status"] == "valid"
    assert Transport(root).dispatch("run", {"spec": specs["rma"], "output": "/"})["code"] == "path_outside_root"


def test_study_tools_are_root_scoped(tmp_path):
    from test_study import community_study
    study = json.loads(community_study(tmp_path).read_text())
    transport = Transport(tmp_path)
    outcome = transport.dispatch("study_run", {"study": study, "output": "study-out"})
    assert outcome["status"] == "complete" and outcome["study_dir"] == "study-out"
    verified = transport.dispatch("study_inspect", {"study_dir": "study-out"})
    assert verified["status"] == "verified" and set(verified["runs"]) == {"describe", "zones"}
    reproduced = transport.dispatch("study_reproduce", {"study_dir": "study-out", "output": "again"})
    assert reproduced["status"] == "reproduced" and reproduced["new"] == "again"
    escaping = json.loads(json.dumps(study))
    escaping["inputs"]["counts"]["path"] = "../outside.dat"
    refused = transport.dispatch("study_run", {"study": escaping, "output": "x"})
    assert refused["code"] == "path_outside_root" and not (tmp_path / "x").exists()


def test_advertised_spec_is_compact_but_calls_are_fully_validated(tmp_path):
    definitions = {d["name"]: d["inputSchema"] for d in tool_definitions()}
    assert len(json.dumps(definitions["run"])) < 1000 and "$defs" not in definitions["run"]
    refused = Transport(tmp_path).dispatch("validate", {"spec": {"method": "community", "input": "x"}})
    assert refused["status"] == "error" and refused["code"] in ("invalid_arguments", "invalid_spec", "invalid_request")


def test_primer_tool_delivery_and_discovery(tmp_path):
    async def scenario():
        async with client(tmp_path) as session:
            assert session.instructions == SERVER_INSTRUCTIONS
            assert session.server_info.version == primer()["version"]
            delivered = unpack(await session.call_tool("primer", {}))
            assert delivered == primer()
            assert (await session.call_tool("primer", {"bundle": "outside"})).is_error
            discovery = unpack(await session.call_tool("discover", {}))
            assert discovery["primer"] == primer_metadata()
            for method in discovery["method_index"]:
                detailed = unpack(await session.call_tool("discover", {"method": method["id"]}))
                assert detailed["primer"] == primer_metadata()
                assert detailed["input_schema"]["properties"]["method"]["const"] == method["id"]

    asyncio.run(scenario())


def test_primer_instructions_and_schemas(tmp_path):
    assert len(SERVER_INSTRUCTIONS) <= 512
    assert "primer tool" in SERVER_INSTRUCTIONS
    assert "never bypass it with bespoke code" in SERVER_INSTRUCTIONS
    assert create_server(tmp_path).create_initialization_options().instructions == SERVER_INSTRUCTIONS
    definitions = {item["name"]: item for item in tool_definitions()}
    schema = definitions["primer"]["inputSchema"]
    assert schema["properties"] == {} and schema["additionalProperties"] is False
    assert "required" not in schema or schema["required"] == []
    for name in ("run", "study_run"):
        assert "Read the primer first" in definitions[name]["description"]
    assert {"rarefaction", "count_homogeneity"} <= set(
        definitions["run"]["inputSchema"]["properties"]["spec"]["properties"]["method"]["enum"])


def test_stdio_neotoma_schema_agrees_with_accepted_requests(tmp_path):
    jsonschema = pytest.importorskip("jsonschema")
    import hashlib
    from test_neotoma import _download, _spec
    data = json.dumps(_download()).encode()
    (tmp_path / "download.json").write_bytes(data)
    request = {"spec": _spec("download.json", hashlib.sha256(data).hexdigest()), "output": "extractions"}

    async def scenario():
        async with client(tmp_path) as session:
            tools = {tool.name: tool for tool in (await session.list_tools()).tools}
            advertised = tools["neotoma_extract"].input_schema
            jsonschema.validate(request, advertised)
            extracted = unpack(await session.call_tool("neotoma_extract", request))
            assert extracted["status"] == "complete"
            assert unpack(await session.call_tool("neotoma_inspect", {"bundle": extracted["bundle"]}))["status"] == "verified"
            wrong = {**request, "spec": {**request["spec"], "method": "community"}}
            with pytest.raises(jsonschema.ValidationError):
                jsonschema.validate(wrong, advertised)
            assert unpack(await session.call_tool("neotoma_extract", wrong))["code"] == "invalid_request"

    asyncio.run(scenario())
