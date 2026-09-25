"""dp-demo — a RiskFoundry code data provider."""

from __future__ import annotations

import os
from collections.abc import Iterator
from typing import Any

import pyodbc
import riskfoundry as rf

# Windows authentication against the local SQL Server instance. No password lives here.
# Override with DP_DEMO_SQL_CONNECTION when the instance or database differs.
_DEFAULT_CONNECTION = (
    "Driver={ODBC Driver 18 for SQL Server};"
    "Server=localhost\\MSSQLSERVERCRAFT;"
    "Database=dummydb;"
    "Trusted_Connection=yes;"
    "TrustServerCertificate=yes;"
)

_QUERY = """
SELECT record_id, input_1, input_2
FROM dbo.DpDemoInputs
ORDER BY record_id
"""


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
    connection = pyodbc.connect(_connection_string(), timeout=30)
    try:
        cursor = connection.cursor()
        cursor.execute(_QUERY)
        for record_id, input_1, input_2 in cursor:
            yield {
                "recordId": str(record_id),
                "values": {"input_1": input_1, "input_2": input_2},
            }
    finally:
        connection.close()


def _connection_string() -> str:
    return os.environ.get("DP_DEMO_SQL_CONNECTION", _DEFAULT_CONNECTION)
