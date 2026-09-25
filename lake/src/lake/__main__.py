"""Start the local lake API.

    uv run python -m lake

Listens on 127.0.0.1:8110 unless LAKE_PORT is set. The file is LAKE_DATA,
defaulting to data/obligors.jsonl beside this project.
"""

from __future__ import annotations

import os
from pathlib import Path

from lake.api import serve
from lake.reader import FolderLake

_DEFAULT_PORT = 8110


def main() -> None:
    path = Path(os.environ.get("LAKE_DATA", str(_default_data())))
    serve(FolderLake(path), _port(os.environ.get("LAKE_PORT", str(_DEFAULT_PORT))))


def _default_data() -> Path:
    return Path(__file__).resolve().parents[2] / "data" / "obligors.jsonl"


def _port(raw: str) -> int:
    try:
        port = int(raw)
    except ValueError as error:
        raise SystemExit(f"LAKE_PORT must be an integer, got {raw!r}") from error
    if port < 1 or port > 65535:
        raise SystemExit(f"LAKE_PORT must be from 1 to 65535, got {raw!r}")
    return port


if __name__ == "__main__":
    main()
