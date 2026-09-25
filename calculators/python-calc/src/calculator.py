"""python-calc — a RiskFoundry code calculator.

Reads one obligor per record (the dp-rest row, with the lake id carried as ``id_``)
and writes ``final_score``, a letter grade from credit score and leverage.
"""

from collections.abc import Iterable, Iterator
from decimal import Decimal
from typing import Any

import riskfoundry as rf
from ref_table import get_score

# Adjusted score floors, best grade first. The key is an index into SCORE_TABLE.
_BANDS: tuple[tuple[int, int], ...] = (
    (780, 3),  # AAA
    (720, 2),  # AA
    (670, 1),  # A
    (630, 6),  # BBB
    (590, 5),  # BB
    (550, 4),  # B
    (510, 9),  # CCC
    (470, 8),  # CC
    (430, 7),  # C
)


def calculate(
    context: rf.InvocationContext,
    records: Iterable[rf.Record],
) -> Iterator[dict[str, Any]]:
    """Produce one output record per input record.

    The names read and written are the ones ``calculator.yaml`` declares. A value
    written under a name no output declares fails the run.
    """
    context.info("scoring", "Calculating final_score")
    for idx, record in enumerate(records, start=1):
        obligor_id = record["id_"]
        sector = record["sector"]
        revenue = record["revenue"]
        credit_score = record["credit_score"]
        ltd_ratio = record["ltd_ratio"]

        adjusted = calc_intermediate(credit_score, ltd_ratio)
        score_key = calc_score_key(adjusted)
        score = get_score(score_key)
        descriptive_score = f"""id_={obligor_id} sector={sector} revenue={revenue}
            credit_score={credit_score} ltd_ratio={ltd_ratio}
            adjusted={adjusted} key={score_key} final_score={score}"""

        context.info(
            "scored",
            descriptive_score,
            record_id=record.id,
        )
        context.progress(idx)
        yield {"recordId": record.id, "values": {"final_score": descriptive_score}}


def calc_intermediate(credit_score: Any, ltd_ratio: Any) -> int:
    """Credit score minus one point per percentage point of LTD ratio.

    ``ltd_ratio`` of 0.35 subtracts 35. A higher result is a stronger obligor.
    """
    penalty = int(_number(ltd_ratio) * 100)
    return int(_number(credit_score)) - penalty


def calc_score_key(adjusted: int) -> int:
    """Map an adjusted score onto a key in the grade table. 10 is the weakest."""
    for floor, key in _BANDS:
        if adjusted >= floor:
            return key
    return 10


def _number(value: Any) -> Decimal:
    if isinstance(value, Decimal):
        return value
    if isinstance(value, int):
        return Decimal(value)
    return Decimal(str(value))
