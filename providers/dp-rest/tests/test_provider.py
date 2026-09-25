"""Tests for the dp-rest provider.

These run locally with `uv run pytest` — no container, no platform connection.
The lake API is not running: `_get_json` is replaced with a page the test owns.
`test_prints_the_values` is the exception: it calls the live API.
"""

from decimal import Decimal

import riskfoundry as rf

import src.provider as provider
from src.provider import build


def context() -> rf.InvocationContext:
    """The context to hand the handler outside a run.

    Progress and diagnostics travel over the protocol channel, so a context that is not
    attached to a run refuses to emit them. The two channels here accept what the handler
    reports.
    """
    invocation = rf.InvocationContext(invocation_id="test")
    invocation._emit_progress = lambda completed, total, message: None
    invocation._emit_diagnostic = lambda severity, code, message, record_id: None
    return invocation


def _row(record_id: str, sector: str, revenue: str, ltd_ratio: str, credit_score: str) -> dict[str, str]:
    return {
        "id": record_id,
        "sector": sector,
        "revenue": revenue,
        "ltd_ratio": ltd_ratio,
        "credit_score": credit_score,
    }


def test_produces_records(monkeypatch):
    pages = {
        None: {
            "records": [
                _row("1", "Technology", "45000000", "0.35", "720"),
                _row("2", "Energy", "12000000", "0.72", "580"),
            ],
            "nextCursor": "2",
        },
        "2": {
            "records": [_row("3", "Healthcare", "28000000", "0.48", "690")],
            "nextCursor": None,
        },
    }
    calls: list[str] = []

    def get_json(url: str):
        calls.append(url)
        cursor = url.split("cursor=", 1)[1] if "cursor=" in url else None
        return pages[cursor]

    monkeypatch.setattr(provider, "_get_json", get_json)
    output = list(build(context()))

    assert [row["recordId"] for row in output] == ["1", "2", "3"]
    assert output[0]["values"]["revenue"] == Decimal("45000000")
    assert output[0]["values"]["ltd_ratio"] == Decimal("0.35")
    assert calls[0].endswith("/records")
    assert "cursor=2" in calls[1]


def test_emits_the_declared_output_fields(monkeypatch):
    """The produced names must match `outputs` in provider.yaml exactly."""
    monkeypatch.setattr(
        provider,
        "_get_json",
        lambda url: {
            "records": [_row("1", "Technology", "45000000", "0.35", "720")],
            "nextCursor": None,
        },
    )
    output = list(build(context()))

    assert set(output[0]["values"]) == {"sector", "revenue", "ltd_ratio", "credit_score"}


def test_streams_rather_than_materializing(monkeypatch):
    calls: list[str] = []

    def get_json(url: str):
        calls.append(url)
        if len(calls) == 1:
            return {
                "records": [_row("1", "Technology", "45000000", "0.35", "720")],
                "nextCursor": "2",
            }
        return {
            "records": [_row("2", "Energy", "12000000", "0.72", "580")],
            "nextCursor": None,
        }

    monkeypatch.setattr(provider, "_get_json", get_json)
    produced = build(context())

    assert next(iter(produced))["recordId"] == "1"
    assert len(calls) == 1


def test_a_bad_number_is_skipped(monkeypatch):
    warnings: list[str] = []
    invocation = context()
    invocation._emit_diagnostic = lambda severity, code, message, record_id: warnings.append(code)
    monkeypatch.setattr(
        provider,
        "_get_json",
        lambda url: {
            "records": [
                _row("1", "Technology", "nope", "0.35", "720"),
                _row("2", "Energy", "12000000", "0.72", "580"),
            ],
            "nextCursor": None,
        },
    )

    output = list(build(invocation))

    assert [row["recordId"] for row in output] == ["2"]
    assert warnings == ["lake_value_unusable"]


def test_prints_the_values():
    """Lists each row. Needs the lake API (`uv run python -m lake` in `lake/`)."""
    output = list(build(context()))
    for row in output:
        values = row["values"]
        print(row["recordId"], values["sector"], values["revenue"], values["ltd_ratio"], values["credit_score"])
