"""The versioned agent primer, loaded from its single packaged source."""

from hashlib import sha256
from importlib import metadata, resources


def primer() -> dict[str, str]:
    body = resources.files("palaeo_agent").joinpath("primer.md").read_bytes()
    try:
        version = metadata.version("palaeo-agent")
    except metadata.PackageNotFoundError:
        from . import __version__

        version = __version__
    return {"version": version, "sha256": sha256(body).hexdigest(), "text": body.decode("utf-8")}


def primer_metadata() -> dict[str, str]:
    document = primer()
    return {"version": document["version"], "sha256": document["sha256"],
            "read_first": "Before any analysis, read the full primer via palaeo_agent.primer(), "
                          "palaeo-agent primer, or the primer tool; use suitable toolkit operations."}
