# dp-rest local API and stand-in data lake

Status: phases 1–3 done. Phase 4 not started.

`dp-rest` calls a small local HTTP API. That API is the only component that knows how the lake is stored. The first lake is a folder of files on this machine.

This work stays in `craftit-dp`. It is not a Craft service. Connector profiles are not handed to provider code yet, and `dp-demo` already reaches a local source the same way: a client in the provider, an address from the environment, nothing in `provider.yaml`.

## Goal

A local run of `dp-rest` reads rows from `GET /records` and yields one dataset record per row.

## Non-goals

- A real lake (blob storage, a warehouse, SQL).
- Platform source profiles (`kind: http` in the manifest). The SDK does not open that profile from the handler yet. `sources` stays `[]`.
- Authentication.
- A sandbox or published run. `provider.yaml` says `execution: both`, but a sandbox cannot see `127.0.0.1` on the laptop. Local runs are the target until the API lives somewhere that environment can reach.

## Ownership

| | |
|---|---|
| Repository | `craftit-dp` (private). Plan path: `docs/plans/dp-rest-local-api.md`. |
| Framework vs product | Product-side demo. No `craft-*` change. |
| craft-core reuse | None. No service, repository, or controller is being added. |
| Source generators | N/A. Python only. |
| Exceptions, logging, telemetry, host registration | N/A for Craft. A bad lake row fails the read with `LakeReadError`. The provider, in a later phase, turns a single bad row into `context.warning` and skips it. A dead API fails the run. |
| API / data / UI | Local JSON API only. No Craft endpoint, no migration, no UI. |
| Compatibility | The HTTP JSON shape below is the contract `dp-rest` will bind to. Field names `id`, `sector`, `revenue`, `ltd_ratio`, and `credit_score` stay stable once the provider declares them. |
| Tests | `uv run pytest` inside `lake/` for the reader and the API. Provider tests stay inside `providers/dp-rest/` until phase 4. |

## Shape

```text
dp-rest  --HTTP-->  local API  --reader-->  lake folder
```

The API and the lake sit beside the provider. A publish copies `providers/dp-rest/` into the image, so the lake must not live in that folder.

```text
craftit-dp/
  providers/dp-rest/          # client only
  lake/
    data/obligors.jsonl       # phase 1, the stand-in lake
    src/lake/reader.py        # phase 1, FolderLake
    src/lake/api.py           # phase 2, GET /records and GET /health
    src/lake/__main__.py      # phase 2, the process
    tests/
```

The provider depends on the HTTP contract. The API depends on `LakeReader`. `FolderLake` reads `obligors.jsonl`. A later reader can load parquet, SQL, or a bucket without changing `dp-rest`.

## Contract

`GET /records` returns one page:

```json
{
  "records": [
    {"id": "1", "sector": "Technology", "revenue": "45000000", "ltd_ratio": "0.35", "credit_score": "720"}
  ],
  "nextCursor": null
}
```

Numbers are strings so they stay exact decimals. `id` becomes `recordId`. The provider declares `sector` (`string`), `revenue`, `ltd_ratio` and `credit_score` (`decimal`). Those are the wire names for the wireframe columns Sector, Revenue, LTD_Ratio and CreditScore. The provider loops while `nextCursor` is set.

Query string on `GET /records`: `cursor` (omit for the first page) and `pageSize` (omit for 100). A bad value, or a `LakeReadError`, is HTTP 400 `{"error": "..."}`. `GET /health` returns `{"status": "ok"}` and does not read the lake.

Base URL comes from `DP_REST_BASE_URL`, default `http://127.0.0.1:8110`. Same idea as `DP_DEMO_SQL_CONNECTION` in `dp-demo`. The URL stays out of `provider.yaml`.

Port **8110**. Port 8099 is the SDK package feed.

The reader speaks the same page, in Python: `Page.records` and `Page.next_cursor`. `next_cursor` is the offset of the next JSONL record, as text. Blank lines do not count.

## Phases

1. **Lake reader.** Done. `FolderLake.read_page` reads `lake/data/obligors.jsonl` and returns pages. One test, no HTTP.
2. **API.** Done. `uv run python -m lake` serves `GET /records` and `GET /health` on `127.0.0.1:8110`. The handler calls `LakeReader`. Only `__main__` opens `obligors.jsonl`, via `FolderLake`. Override the file with `LAKE_DATA` and the port with `LAKE_PORT`.
3. **Provider.** Done. `build` pages `GET /records` with `urllib` (no new package, so `uv.lock` is unchanged). `DP_REST_BASE_URL` overrides `http://127.0.0.1:8110`. `provider.yaml` declares `sector`, `revenue`, `ltd_ratio` and `credit_score`. `id` is `recordId`. A bad number is `context.warning("lake_value_unusable")` and the row is skipped. The scaffold tests replace `_get_json`, so they do not need the API.
4. **Tests and the local run.** Provider tests use a fake HTTP response, so `riskfoundry test` does not need the server. The live check is: start the API, then `uv run riskfoundry provider run --manifest provider.yaml --print 5`.

## Validation

From `lake/`:

```powershell
cd C:\repo-priv-dp\craftit-dp\lake
uv sync
uv run pytest
```

The reader test walks `obligors.jsonl` in pages of two and checks the last page has no cursor. The API tests check the JSON contract, that `pageSize` is forwarded, and that `/health` answers on a real socket.

Start the API:

```powershell
uv run python -m lake
```
