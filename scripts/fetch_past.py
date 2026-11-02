#!/usr/bin/env python3
"""Download the legacy PAST 2001 example datasets and verify their SHA-256.

The datasets are not redistributed here (except dielasma.dat and llanvirn.dat).
Files land at the paths recorded in benchmarks/past/legacy-cases.json, which
are git-ignored; existing files that already match their checksum are kept.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
import urllib.error
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
INVENTORY = ROOT / "benchmarks" / "past" / "legacy-cases.json"
USER_AGENT = "Mozilla/5.0"


def inventory() -> dict[str, dict]:
    cases = json.loads(INVENTORY.read_text())["cases"]
    return {item["filename"]: item for case in cases for item in case["files"]}


def sha256(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def ensure(names=None, *, check_only: bool = False) -> list[str]:
    """Make the named files (default: all) present and verified; return problems."""
    files = inventory()
    problems = []
    for name in sorted(files if names is None else names):
        item = files[name]
        path = ROOT / item["path"]
        if path.exists():
            if sha256(path.read_bytes()) == item["sha256"]:
                continue
            problems.append(f"{name}: local file does not match the recorded SHA-256")
            continue
        if check_only:
            problems.append(f"{name}: missing")
            continue
        try:
            request = urllib.request.Request(item["url"], headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(request, timeout=30) as response:
                content = response.read()
        except (urllib.error.URLError, TimeoutError) as exc:
            problems.append(f"{name}: download failed ({exc})")
            continue
        if sha256(content) != item["sha256"]:
            problems.append(f"{name}: downloaded bytes do not match the recorded SHA-256; not written")
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
        print(f"fetched {name}")
    return problems


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true",
                        help="Verify existing files without downloading anything.")
    args = parser.parse_args()
    problems = ensure(check_only=args.check)
    for problem in problems:
        print(f"UNRESOLVED {problem}", file=sys.stderr)
    if not problems:
        print(f"All {len(inventory())} legacy datasets present and verified.")
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
