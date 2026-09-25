"""Tests for the python-calc calculator.

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
    return rf.InvocationContext(
        invocation_id="test",
        _emit_progress=lambda completed, total, message: None,
        _emit_diagnostic=lambda severity, code, message, record_id: None,
    )


def record(record_id: str, **values) -> rf.Record:
    """An input record. `rf.Record` is the type your handler is given, so tests use it too."""
    return rf.Record(record_id, values, {})


def test_emits_one_output_per_input():
    records = [record("r1", id_=1000, sector="sample", revenue=1000, credit_score=1000, ltd_ratio=1000), record("r2", id_=1000, sector="sample", revenue=1000, credit_score=1000, ltd_ratio=1000)]

    output = list(calculate(context(), records))

    assert [row["recordId"] for row in output] == ["r1", "r2"]


def test_emits_the_declared_output_fields():
    """The output names must match `outputs` in calculator.yaml exactly.

    A value written under a name no output declares fails the run — it is not dropped — so this
    assertion is the cheapest place to notice a rename.
    """
    output = list(calculate(context(), [record("r1", id_=1000, sector="sample", revenue=1000, credit_score=1000, ltd_ratio=1000)]))

    assert set(output[0]["values"]) == {"final_score", "descriptive_score"}
    # credit_score 1000 minus ltd_ratio 1000 (as percent) falls off the bottom of the table.
    assert output[0]["values"]["final_score"] == "-"


def test_scores_lake_obligors_from_credit_and_leverage():
    """The six dp-rest rows, with the lake id carried as id_."""
    rows = [
        ("1", 1, "Technology", "45000000", "720", "0.35", "A"),
        ("2", 2, "Energy", "12000000", "580", "0.72", "CC"),
        ("3", 3, "Healthcare", "28000000", "690", "0.48", "BBB"),
        ("4", 4, "Technology", "95000000", "810", "0.15", "AAA"),
        ("5", 5, "Energy", "8500000", "640", "0.61", "B"),
        ("6", 6, "Healthcare", "62000000", "750", "0.01", "AA"),
    ]
    records = [
        record(
            record_id,
            id_=obligor_id,
            sector=sector,
            revenue=revenue,
            credit_score=credit_score,
            ltd_ratio=ltd_ratio,
        )
        for record_id, obligor_id, sector, revenue, credit_score, ltd_ratio, _grade in rows
    ]

    output = list(calculate(context(), records))

    assert [row["values"]["final_score"] for row in output] == [grade for *_, grade in rows]
