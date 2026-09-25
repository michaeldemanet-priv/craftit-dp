"""Read pages of records from a stand-in data lake.

The provider never opens this folder. The local API will call a LakeReader,
and FolderLake is the first one: a single JSONL file. Numbers stay text
so a later decimal conversion cannot turn them into floats.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Protocol

DEFAULT_PAGE_SIZE = 100


class LakeReadError(Exception):
    """The lake file cannot be read as records."""


@dataclass(frozen=True)
class Record:
    id: str
    sector: str
    revenue: str
    ltd_ratio: str
    credit_score: str


@dataclass(frozen=True)
class Page:
    records: tuple[Record, ...]
    next_cursor: str | None


class LakeReader(Protocol):
    def read_page(self, *, cursor: str | None = None, page_size: int = DEFAULT_PAGE_SIZE) -> Page:
        """Return one page. ``next_cursor`` is set when another page follows."""


class FolderLake:
    """A lake stored as one JSONL file."""

    def __init__(self, path: Path) -> None:
        self._path = path

    def read_page(self, *, cursor: str | None = None, page_size: int = DEFAULT_PAGE_SIZE) -> Page:
        start = _cursor_offset(cursor)
        if page_size < 1:
            raise LakeReadError("page_size must be at least 1")

        collected: list[Record] = []
        seen = 0
        overflow = False
        with self._path.open(encoding="utf-8") as handle:
            for line_number, raw in enumerate(handle, start=1):
                if not raw.strip():
                    continue
                if seen < start:
                    seen += 1
                    continue
                if len(collected) == page_size:
                    overflow = True
                    break
                collected.append(_record(raw, line_number))
                seen += 1

        next_cursor = str(start + page_size) if overflow else None
        return Page(tuple(collected), next_cursor)


def _cursor_offset(cursor: str | None) -> int:
    if cursor is None:
        return 0
    try:
        offset = int(cursor)
    except ValueError as error:
        raise LakeReadError(f"cursor is not an offset: {cursor}") from error
    if offset < 0:
        raise LakeReadError(f"cursor is negative: {cursor}")
    return offset


def _record(raw: str, line_number: int) -> Record:
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as error:
        raise LakeReadError(f"line {line_number} is not JSON") from error
    if not isinstance(payload, Mapping):
        raise LakeReadError(f"line {line_number} is not an object")

    record_id = _text(payload, "id", line_number)
    sector = _text(payload, "sector", line_number)
    return Record(
        id=record_id,
        sector=sector,
        revenue=_decimal(payload, "revenue", line_number),
        ltd_ratio=_decimal(payload, "ltd_ratio", line_number),
        credit_score=_decimal(payload, "credit_score", line_number),
    )


def _decimal(payload: Mapping[str, object], name: str, line_number: int) -> str:
    text = _text(payload, name, line_number)
    try:
        Decimal(text)
    except InvalidOperation as error:
        raise LakeReadError(f"line {line_number} {name} is not a decimal") from error
    return text


def _text(payload: Mapping[str, object], name: str, line_number: int) -> str:
    value = payload.get(name)
    if not isinstance(value, str) or value == "":
        raise LakeReadError(f"line {line_number} {name} must be a non-empty string")
    return value
