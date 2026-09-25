"""HTTP API over a LakeReader.

The handler never opens the lake file. The process in ``__main__`` builds a
FolderLake and passes it in. ``GET /records`` speaks the JSON contract in
``docs/plans/dp-rest-local-api.md``.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any
from urllib.parse import parse_qs, urlsplit

from lake.reader import DEFAULT_PAGE_SIZE, LakeReadError, LakeReader

JsonBody = dict[str, Any]


class ApiError(Exception):
    """The request cannot be served. Mapped to HTTP 400."""


def handle_request(method: str, target: str, reader: LakeReader) -> tuple[int, JsonBody]:
    """Answer one request. ``target`` is the path plus query string."""
    if method != "GET":
        return 405, {"error": "method not allowed"}

    parsed = urlsplit(target)
    if parsed.path == "/health":
        return 200, {"status": "ok"}
    if parsed.path != "/records":
        return 404, {"error": "not found"}

    try:
        query = parse_qs(parsed.query, keep_blank_values=True)
        page = reader.read_page(cursor=_cursor(query), page_size=_page_size(query))
    except (ApiError, LakeReadError) as error:
        return 400, {"error": str(error)}

    return 200, {
        "records": [
            {
                "id": record.id,
                "sector": record.sector,
                "revenue": record.revenue,
                "ltd_ratio": record.ltd_ratio,
                "credit_score": record.credit_score,
            }
            for record in page.records
        ],
        "nextCursor": page.next_cursor,
    }


def serve(reader: LakeReader, port: int, host: str = "127.0.0.1") -> None:
    """Serve until interrupted. Binds ``host`` only."""
    server = ThreadingHTTPServer((host, port), make_handler(reader))
    print(f"listening on http://{host}:{port}", flush=True)
    try:
        server.serve_forever()
    finally:
        server.server_close()


def make_handler(reader: LakeReader) -> type[BaseHTTPRequestHandler]:
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802 — stdlib name
            status, body = handle_request("GET", self.path, reader)
            payload = json.dumps(body).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

        def log_message(self, fmt: str, *args: object) -> None:
            print(f"{self.address_string()} {fmt % args}", flush=True)

    return Handler


def _cursor(query: Mapping[str, list[str]]) -> str | None:
    values = query.get("cursor")
    if not values:
        return None
    if len(values) != 1 or values[0] == "":
        raise ApiError("cursor must be a single value")
    return values[0]


def _page_size(query: Mapping[str, list[str]]) -> int:
    values = query.get("pageSize")
    if not values:
        return DEFAULT_PAGE_SIZE
    if len(values) != 1:
        raise ApiError("pageSize must be a single value")
    try:
        size = int(values[0])
    except ValueError as error:
        raise ApiError("pageSize must be an integer") from error
    if size < 1:
        raise ApiError("pageSize must be at least 1")
    return size
