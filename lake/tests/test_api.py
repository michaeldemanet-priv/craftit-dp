"""The HTTP handler calls a LakeReader and does not open the lake file."""

import json
from http.server import ThreadingHTTPServer
from pathlib import Path
from threading import Thread
from urllib.request import urlopen

from lake.api import handle_request, make_handler
from lake.reader import DEFAULT_PAGE_SIZE, FolderLake, LakeReadError, Page, Record

OBLIGORS = Path(__file__).resolve().parents[1] / "data" / "obligors.jsonl"


class RecordingLake:
    def __init__(self) -> None:
        self.calls: list[tuple[str | None, int]] = []

    def read_page(self, *, cursor: str | None = None, page_size: int = DEFAULT_PAGE_SIZE) -> Page:
        self.calls.append((cursor, page_size))
        return Page(
            records=(
                Record(
                    id="1",
                    sector="Technology",
                    revenue="45000000",
                    ltd_ratio="0.35",
                    credit_score="720",
                ),
            ),
            next_cursor="2",
        )


def test_records_forwards_cursor_and_page_size():
    lake = RecordingLake()

    status, body = handle_request("GET", "/records?cursor=2&pageSize=2", lake)

    assert status == 200
    assert body == {
        "records": [
            {
                "id": "1",
                "sector": "Technology",
                "revenue": "45000000",
                "ltd_ratio": "0.35",
                "credit_score": "720",
            }
        ],
        "nextCursor": "2",
    }
    assert lake.calls == [("2", 2)]
    assert lake.calls[0][1] != DEFAULT_PAGE_SIZE


def test_records_reads_obligors_through_the_reader():
    status, body = handle_request("GET", "/records?pageSize=2", FolderLake(OBLIGORS))

    assert status == 200
    assert body["records"] == [
        {
            "id": "1",
            "sector": "Technology",
            "revenue": "45000000",
            "ltd_ratio": "0.35",
            "credit_score": "720",
        },
        {
            "id": "2",
            "sector": "Energy",
            "revenue": "12000000",
            "ltd_ratio": "0.72",
            "credit_score": "580",
        },
    ]
    assert body["nextCursor"] == "2"


def test_health_does_not_read_and_a_bad_page_is_refused():
    lake = RecordingLake()

    status, body = handle_request("GET", "/health", lake)
    assert status == 200
    assert body == {"status": "ok"}

    status, body = handle_request("GET", "/records?pageSize=0", lake)
    assert status == 400
    assert lake.calls == []


def test_a_lake_read_error_is_http_400():
    class BrokenLake:
        def read_page(self, *, cursor: str | None = None, page_size: int = DEFAULT_PAGE_SIZE) -> Page:
            raise LakeReadError("line 2 is not JSON")

    status, body = handle_request("GET", "/records", BrokenLake())

    assert status == 400
    assert body == {"error": "line 2 is not JSON"}


def test_server_serves_health():
    server = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(RecordingLake()))
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        port = server.server_address[1]
        with urlopen(f"http://127.0.0.1:{port}/health") as response:
            assert response.status == 200
            assert json.load(response) == {"status": "ok"}
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)
