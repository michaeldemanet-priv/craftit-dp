"""test-dp-cacl — a RiskFoundry code calculator."""

from collections.abc import Iterable, Iterator
from typing import Any

import riskfoundry as rf


def calculate(
    context: rf.InvocationContext,
    records: Iterable[rf.Record],
) -> Iterator[dict[str, Any]]:
    """Produce one output record per input record.

    Args:
        context: Run metadata, progress reporting and diagnostics. ``context.progress(n)`` and
            ``context.warning(code, message)`` are the two you will reach for; your editor knows the
            rest, because the SDK ships its types.
        records: The input records, streamed. Iterate once; do not materialize the whole input.

    Yields:
        One mapping per input record: ``recordId`` correlates the output back to its input, and
        ``values`` holds the calculated fields. Output may be emitted in any order — correlation is by
        ``recordId``, never by position.

    The names you may read and write are the ones ``calculator.yaml`` declares under ``inputs`` and
    ``outputs``. A record carries exactly the declared inputs, and a value written under a name no
    output declares fails the run rather than being dropped.
    """
    for record in records:
        yield {"recordId": record.id, "values": {"output_1": record["input_1"] + 1}}
