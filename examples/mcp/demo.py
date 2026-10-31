"""Run three methods, a refusal and a fresh-process reproduction via MCP."""

import argparse
import asyncio
import json
from pathlib import Path
import shutil
import sys

from mcp import Client, StdioServerParameters

REPO = Path(__file__).resolve().parents[2]


def connection(root):
    return Client(StdioServerParameters(command=sys.executable,
                  args=["-m", "palaeo_agent.mcp_server", "--root", str(root)]))


def checked(result):
    value = result.structured_content
    if result.is_error:
        raise RuntimeError(json.dumps(value))
    return value


async def demo(root):
    root.mkdir(parents=True, exist_ok=False)
    specs = []
    for source in ("dielasma-l2", "community-llanvirn-raw", "permanova-llanvirn"):
        location = REPO / "examples" / f"{source}.json"
        spec = json.loads(location.read_text())
        for field in ("input", "metadata"):
            if spec.get(field):
                source_file = (location.parent / spec[field]).resolve()
                target = f"{source}-{field}{source_file.suffix}"
                shutil.copyfile(source_file, root / target)
                spec[field] = target
        specs.append(spec)
    records = []
    async with connection(root) as client:
        records.append({"discover": checked(await client.call_tool("discover", {}))})
        for spec in specs:
            outcome = checked(await client.call_tool("run", {"spec": spec}))
            records.append(outcome)
        refusal = await client.call_tool("validate", {"spec": {**specs[-1], "design": "repeated"}})
        assert refusal.is_error
        records.append({"unsupported_design": refusal.structured_content})
    async with connection(root) as fresh_client:
        for record in records[1:4]:
            repeated = checked(await fresh_client.call_tool("reproduce", {"bundle": record["run_dir"]}))
            assert repeated["status"] == "reproduced"
            record["reproduction"] = repeated
    (root / "receipt.json").write_text(json.dumps(records, indent=2) + "\n")
    print(json.dumps(records, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path, help="New directory for inputs, bundles and receipt")
    asyncio.run(demo(parser.parse_args().output.resolve()))
