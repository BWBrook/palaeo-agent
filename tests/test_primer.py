import hashlib
from importlib import import_module, metadata, resources
import subprocess
import sys

from palaeo_agent import discover
from palaeo_agent.primer import primer, primer_metadata


def test_primer_matches_packaged_utf8_bytes():
    import palaeo_agent

    body = resources.files("palaeo_agent").joinpath("primer.md").read_bytes()
    document = primer()
    assert palaeo_agent.primer() == document
    assert set(document) == {"version", "sha256", "text"}
    assert document["version"] == metadata.version("palaeo-agent")
    assert document["text"].encode("utf-8") == body
    assert document["sha256"] == hashlib.sha256(body).hexdigest()
    assert "§" in document["text"] and "×" in document["text"]
    assert "†" not in document["text"]
    assert "Bootstrap for a new session" in document["text"]


def test_primer_does_not_normalize_resource_bytes(monkeypatch, tmp_path):
    body = "Unicode: α × §\r\nNo final newline".encode("utf-8")
    (tmp_path / "primer.md").write_bytes(body)
    module = import_module("palaeo_agent.primer")
    monkeypatch.setattr(module.resources, "files", lambda package: tmp_path)
    document = primer()
    assert document["text"].encode("utf-8") == body
    assert document["sha256"] == hashlib.sha256(body).hexdigest()


def test_uninstalled_checkout_uses_package_version(monkeypatch):
    import palaeo_agent

    def unavailable(name):
        raise metadata.PackageNotFoundError(name)

    monkeypatch.setattr(metadata, "version", unavailable)
    assert primer()["version"] == palaeo_agent.__version__


def test_cli_primer_has_header_and_exact_body():
    document = primer()
    command = subprocess.run([sys.executable, "-m", "palaeo_agent", "primer"],
                             capture_output=True, check=True)
    header = f"Palaeo-Agent primer — version {document['version']}\nSHA-256: {document['sha256']}\n\n"
    assert command.stdout == (header + document["text"]).encode("utf-8")
    assert command.stderr == b""


def test_python_and_cli_discovery_point_to_full_primer():
    import json

    pointer = primer_metadata()
    assert set(pointer) == {"version", "sha256", "read_first"}
    assert pointer["sha256"] == primer()["sha256"]
    assert "Before any analysis" in pointer["read_first"]
    assert discover()["primer"] == pointer
    command = subprocess.run([sys.executable, "-m", "palaeo_agent", "discover"],
                             capture_output=True, text=True, check=True)
    assert json.loads(command.stdout)["primer"] == pointer
