"""MCP-only access to a confined scientific worker.

This server is a trusted supervisor component. It never interprets model code
or opens model-selected paths outside Worker.run_python.
"""

import argparse
import asyncio
import json
from pathlib import Path

from .worker import Worker


EXECUTION_TOOLS = [
    {"name": "worker_execute", "description": "Execute Python in the trial. No network, subprocesses, credentials or outside files. Installed scientific packages are available.",
     "inputSchema": {"type": "object", "properties": {"code": {"type": "string", "maxLength": 262144}},
                     "required": ["code"], "additionalProperties": False}},
    {"name": "worker_read", "description": "Read a UTF-8 trial file in a bounded page; paths are relative to the trial root.",
     "inputSchema": {"type": "object", "properties": {"path": {"type": "string"},
                     "offset": {"type": "integer", "minimum": 0, "default": 0},
                     "limit": {"type": "integer", "minimum": 1, "maximum": 32768, "default": 32768}},
                     "required": ["path"], "additionalProperties": False}},
    {"name": "worker_write", "description": "Write a UTF-8 trial file; paths are relative to the trial root.",
     "inputSchema": {"type": "object", "properties": {"path": {"type": "string"},
                     "content": {"type": "string", "maxLength": 262144}},
                     "required": ["path", "content"], "additionalProperties": False}},
]


class ExecutionTransport:
    def __init__(self, worker, *, toolkit=False):
        self.worker = worker
        self.tools = list(EXECUTION_TOOLS)
        self.palaeo_names = set()
        if toolkit:
            discovery = worker.run_python(["-c", "import json; from palaeo_agent.mcp_server import tool_definitions; print(json.dumps(tool_definitions()))"],
                                          request={"tool": "supervisor_load_tool_definitions"})
            if discovery["status"] != "ok" or discovery["truncated"]["stdout"]:
                raise ValueError(f"Cannot discover confined toolkit tools: {discovery}")
            for tool in json.loads(discovery["stdout"]):
                self.palaeo_names.add(tool["name"])
                self.tools.append({**tool, "name": "palaeo_" + tool["name"]})
        (worker.log_dir / "tools.json").write_text(json.dumps(self.tools, indent=2) + "\n")

    def dispatch(self, name, arguments):
        definitions = {tool["name"]: tool for tool in self.tools}
        if name not in definitions or not isinstance(arguments, dict):
            return self.worker.reject({"tool": name, "arguments": arguments}, "Unknown tool or malformed arguments")
        schema = definitions[name]["inputSchema"]
        properties = schema.get("properties", {})
        if set(arguments) - set(properties) or set(schema.get("required", [])) - set(arguments):
            return self.worker.reject({"tool": name, "arguments": arguments}, "Missing or unknown arguments")
        try:
            if name == "worker_execute":
                return self.worker.execute(**arguments)
            if name == "worker_read":
                return self.worker.read(**arguments)
            if name == "worker_write":
                return self.worker.write(**arguments)
            result = self.worker.palaeo(name.removeprefix("palaeo_"), arguments)
            if result.get("truncated", {}).get("stdout"):
                return {"status": "error", "code": "output_limit", "execution": result}
            try:
                value = json.loads(result["stdout"])
            except (ValueError, KeyError):
                return {"status": "error", "code": "worker_failed", "execution": result}
            if result["status"] not in ("ok", "error") or result["exit_code"] not in (0, 2):
                return {"status": "error", "code": "worker_failed", "execution": result}
            return value
        except (TypeError, ValueError) as exc:
            return self.worker.reject({"tool": name, "arguments": arguments}, str(exc))


def create_server(transport):
    from mcp import types
    from mcp.server import Server

    async def list_tools(context, params):
        return types.ListToolsResult(tools=[types.Tool.model_validate(tool) for tool in transport.tools])

    async def call_tool(context, params):
        value = await asyncio.to_thread(transport.dispatch, params.name, params.arguments or {})
        return types.CallToolResult(content=[types.TextContent(type="text", text=json.dumps(value, allow_nan=False))],
                                    structured_content=value, is_error=value.get("status") in ("error", "timed_out", "different"))

    return Server("confined-scientific-worker", version="1", on_list_tools=list_tools, on_call_tool=call_tool)


async def serve(config):
    from mcp.server.stdio import stdio_server
    config = dict(config)
    toolkit = config.pop("toolkit", False)
    transport = ExecutionTransport(Worker(**config), toolkit=toolkit)
    server = create_server(transport)
    async with stdio_server() as (read, write):
        await server.run(read, write, server.create_initialization_options())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    args = parser.parse_args()
    asyncio.run(serve(json.loads(args.config.read_text())))


if __name__ == "__main__":
    main()
