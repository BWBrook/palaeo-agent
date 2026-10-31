"""Structured command-line access to the same Python implementation."""

import argparse
import json
from pathlib import Path
import sys

from pydantic import ValidationError

from .core import AnalysisError
from .methods import METHOD_INDEX, discover, parse_spec, validate
from .runs import inspect_run, reproduce, run
from .sensitivity import compare_community_runs, inspect_comparison


class JsonArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        raise AnalysisError("invalid_arguments", message)


def _spec(path):
    spec_path = Path(path).resolve()
    spec = parse_spec(json.loads(spec_path.read_text(encoding="utf-8")))
    if not spec.input.is_absolute():
        spec = spec.model_copy(update={"input": (spec_path.parent / spec.input).resolve()})
    if getattr(spec, "metadata", None) is not None and not spec.metadata.is_absolute():
        spec = spec.model_copy(update={"metadata": (spec_path.parent / spec.metadata).resolve()})
    return spec


def main(argv=None):
    parser = JsonArgumentParser(prog="palaeo-agent", description=(
        "Supported methods: " + ", ".join(method["id"] for method in METHOD_INDEX) +
        ". Use discover for method summaries and complete input/output schemas."
    ))
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("discover")
    for command in ("validate", "run"):
        sub = commands.add_parser(command)
        sub.add_argument("spec")
        if command == "run":
            sub.add_argument("--output", required=True)
    for command in ("inspect", "reproduce", "inspect-comparison"):
        sub = commands.add_parser(command)
        sub.add_argument("run_dir")
        if command == "reproduce":
            sub.add_argument("--output", required=True)
    comparison = commands.add_parser("compare")
    comparison.add_argument("baseline")
    comparison.add_argument("sensitivity")
    comparison.add_argument("--output", required=True)
    try:
        args = parser.parse_args(argv)
        match args.command:
            case "discover":
                result = discover()
            case "validate":
                result = validate(_spec(args.spec))
            case "run":
                result = run(_spec(args.spec), args.output)
            case "inspect":
                result = inspect_run(args.run_dir)
            case "reproduce":
                result = reproduce(args.run_dir, args.output)
            case "compare":
                result = compare_community_runs(args.baseline, args.sensitivity, args.output)
            case "inspect-comparison":
                result = inspect_comparison(args.run_dir)
        print(json.dumps(result, allow_nan=False))
        return 1 if result.get("status") == "different" else 0
    except ValidationError as exc:
        error = {"status": "error", "code": "invalid_specification", "message": "Request does not match the method schema",
                 "details": json.loads(exc.json(include_url=False, include_context=False))}
    except AnalysisError as exc:
        error = exc.as_dict()
    except (OSError, ValueError) as exc:
        error = {"status": "error", "code": "request_unreadable", "message": str(exc)}
    print(json.dumps(error, allow_nan=False), file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
