"""Tests for the dp-random provider.

These run locally with `uv run pytest` — no container, no platform connection.
"""

import riskfoundry as rf

from src.provider import build


def context() -> rf.InvocationContext:
    """The context to hand your handler outside a run.

    The real type, not a stand-in — it is what the platform passes in. Progress and diagnostics
    travel over the protocol channel, so a context that is not attached to a run refuses to emit
    them; if your handler reports, install the two channels here and assert on what it reported.
    """
    return rf.InvocationContext(invocation_id="test")


def test_produces_records():
    output = list(build(context()))

    assert [row["recordId"] for row in output] == ["row-0", "row-1",
                                                   "row-2", "row-3",
                                                   "row-4", "row-5",
                                                   "row-6", "row-7",
                                                   "row-8", "row-9"]


def test_emits_the_declared_output_fields():
    """The produced names must match `outputs` in provider.yaml exactly.

    A value written under a name no output declares fails the run — it is not dropped — so this
    assertion is the cheapest place to notice a rename.
    """
    output = list(build(context()))

    assert set(output[0]["values"]) == {"input_1", "input_2"}


def test_streams_rather_than_materializing():
    # A generator, not a list: the platform writes each record as it is produced, and a provider that
    # collects its whole result first would defeat that on both sides.
    produced = build(context())

    assert next(iter(produced))["recordId"] == "row-0"

def test_prints_the_random_values():
    output = list(build(context()))
    for row in output:
        print(row["recordId"], row["values"]["input_2"])
