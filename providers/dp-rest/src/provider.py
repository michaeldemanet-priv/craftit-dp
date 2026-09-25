"""dp-rest — a RiskFoundry code data provider.

Reads pages from the local lake API. The base URL is ``DP_REST_BASE_URL``,
defaulting to ``http://127.0.0.1:8110``. Nothing in this file opens the lake.
"""

from __future__ import annotations

import json
import os
from collections.abc import Iterator, Mapping
from decimal import Decimal, InvalidOperation
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import urlopen

import riskfoundry as rf

_DEFAULT_BASE_URL = "http://127.0.0.1:8110"
_TIMEOUT_SECONDS = 30


def build(context: rf.InvocationContext) -> Iterator[dict[str, Any]]:
    """Yield one dataset record per lake row.

    Pages until ``nextCursor`` is empty. A row with a missing id or a number that
    is not a decimal is skipped and reported. An unreachable API fails the run.
    """
    produced = 0
    cursor: str | None = None
    while True:
        page = _page(cursor)
        for row in page["records"]:
            record = _record(context, row)
            if record is None:
                continue
            yield record
            produced += 1
            context.progress(produced)
        next_cursor = page.get("nextCursor")
        if not isinstance(next_cursor, str) or next_cursor == "":
            break
        cursor = next_cursor


def _base_url() -> str:
    return os.environ.get("DP_REST_BASE_URL", _DEFAULT_BASE_URL).rstrip("/")


def _page(cursor: str | None) -> Mapping[str, Any]:
    query = {} if cursor is None else {"cursor": cursor}
    url = f"{_base_url()}/records"
    if query:
        url = f"{url}?{urlencode(query)}"
    return _get_json(url)


def _get_json(url: str) -> Mapping[str, Any]:
    try:
        with urlopen(url, timeout=_TIMEOUT_SECONDS) as response:
            status = response.status
            raw = response.read()
    except HTTPError as error:
        status = error.code
        raw = error.read()
    except URLError as error:
        raise RuntimeError(f"lake API is unreachable at {_base_url()}") from error

    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as error:
        raise RuntimeError(f"lake API at {url} did not return JSON") from error

    if status != 200:
        message = payload.get("error") if isinstance(payload, dict) else None
        raise RuntimeError(str(message) if message else f"lake API returned HTTP {status}")
    if not isinstance(payload, dict) or not isinstance(payload.get("records"), list):
        raise RuntimeError("lake API response has no records")
    return payload


def _record(context: rf.InvocationContext, row: Any) -> dict[str, Any] | None:
    if not isinstance(row, dict):
        context.warning("lake_row_unusable", "record is not an object")
        return None

    record_id = row.get("id")
    if not isinstance(record_id, str) or record_id == "":
        context.warning("lake_row_unusable", "record has no id")
        return None

    sector = row.get("sector")
    if not isinstance(sector, str) or sector == "":
        context.warning("lake_row_unusable", "record has no sector", record_id=record_id)
        return None

    values: dict[str, Any] = {"sector": sector}
    for name in ("revenue", "ltd_ratio", "credit_score"):
        number = _decimal(context, record_id, name, row.get(name))
        if number is None:
            return None
        values[name] = number
    return {"recordId": record_id, "values": values}


def _decimal(
    context: rf.InvocationContext, record_id: str, name: str, text: Any
) -> Decimal | None:
    if not isinstance(text, str) or text == "":
        context.warning("lake_value_unusable", f"{name} is missing", record_id=record_id)
        return None
    try:
        return Decimal(text)
    except InvalidOperation:
        context.warning("lake_value_unusable", f"{name} is not a decimal: {text}", record_id=record_id)
        return None
