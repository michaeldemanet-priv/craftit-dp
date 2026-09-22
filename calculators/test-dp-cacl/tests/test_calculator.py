"""Tests for the test-dp-cacl calculator.

These run locally with `uv run pytest` — no container, no platform connection.
"""

import riskfoundry as rf

from src.calculator import calculate


def context() -> rf.InvocationContext:
    """The context to hand your handler outside a run.

    The real type, not a stand-in — it is what the platform passes in. Progress and diagnostics
    travel over the protocol channel, so a context that is not attached to a run refuses to emit
    them; if your handler reports, install the two channels here and assert on what it reported.
    """
    return rf.InvocationContext(invocation_id="test")


def record(record_id: str, **values) -> rf.Record:
    """An input record. `rf.Record` is the type your handler is given, so tests use it too."""
    return rf.Record(record_id, values, {})


def test_emits_one_output_per_input():
    records = [record("r1", input_1=1000, input_2=1000), record("r2", input_1=1000, input_2=1000)]

    output = list(calculate(context(), records))

    assert [row["recordId"] for row in output] == ["r1", "r2"]


def test_emits_the_declared_output_fields():
    """The output names must match `outputs` in calculator.yaml exactly.

    A value written under a name no output declares fails the run — it is not dropped — so this
    assertion is the cheapest place to notice a rename.
    """
    output = list(calculate(context(), [record("r1", input_1=1000, input_2=1000)]))

    assert set(output[0]["values"]) == {"output_1"}
    assert output[0]["values"]["output_1"] == 1001
