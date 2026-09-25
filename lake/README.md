# lake

A local stand-in for a data lake, and the HTTP API that `dp-rest` calls.

The provider never opens the files in this folder. It calls `GET /records` on this process. The API is the only piece that reads `data/obligors.jsonl`. Those six rows are the wireframe test population (sector, revenue, leverage, credit score). A later reader can load something else without changing `dp-rest`.

This process is not started by the provider, by `riskfoundry test`, or by PyCharm. Leave it running in its own terminal. Stopping it makes the live provider run and `test_prints_the_values` fail to connect. The other provider tests use a fake page and do not need it.

A published or sandbox run cannot see `127.0.0.1` on this laptop. This API is for local runs.

## Start the API

From this folder:

```powershell
uv sync
uv run python -m lake
```

Leave that window open. It prints `listening on http://127.0.0.1:8110` and keeps serving until you stop it (Ctrl+C).

Port **8110**. Port 8099 is the SDK package feed. Do not reuse it.

In PyCharm, use a second Python run configuration and leave it running:

- Module name: `lake`
- Working directory: this folder
- Interpreter: `.venv\Scripts\python.exe`

Then run the provider from `providers/dp-rest`.

## What it serves

| Request | Result |
|---|---|
| `GET /health` | `{"status": "ok"}` |
| `GET /records` | One page of obligors. `pageSize` defaults to 100. `cursor` asks for the next page. |
| A bad `pageSize` or `cursor` | HTTP 400 `{"error": "..."}` |

`dp-rest` uses `http://127.0.0.1:8110` unless `DP_REST_BASE_URL` is set.

`LAKE_PORT` changes the port. `LAKE_DATA` points at a different JSONL file. Both are optional.
