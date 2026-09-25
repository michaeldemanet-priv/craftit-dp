"""dp-random — a RiskFoundry code data provider."""

import random
from collections.abc import Iterator
from typing import Any

import riskfoundry as rf


def build(context: rf.InvocationContext) -> Iterator[dict[str, Any]]:
    """Produce the records that populate the destination dataset.

    Args:
        context: Run metadata, progress reporting and diagnostics. A provider handler takes this
            alone — unlike a calculator, it has no input stream to consume. ``context.progress(n)``
            and ``context.warning(code, message)`` are the two you will reach for; your editor knows
            the rest, because the SDK ships its types.

    Yields:
        One mapping per record: ``recordId`` is this record's stable identity within the dataset, and
        ``values`` holds its fields.

    The names you may write are the ones ``provider.yaml`` declares under ``outputs``. A value
    written under a name no output declares fails the run rather than being dropped, and a declared
    name the handler never writes arrives as a null.
    """
    for number in range(10):
        yield {"recordId": f"row-{number}", "values": {"input_1": number + 1, "input_2": random.randint(0, 100)}}