# test-dp-cacl

A code calculator.

A RiskFoundry code calculator. Its entry point is `calculate` in `src/calculator.py`, as
declared by `handler` in `calculator.yaml`.

Local runs are for development. The container run is the truth: the builder image remains the
publish gate, local runs enforce limits only with `--limits`, they do not isolate the network, and
they may run on a different Python patch level than the image (`riskfoundry doctor` warns).

## Layout

| Path | What it is |
|---|---|
| `calculator.yaml` | The manifest. Declares the runtime, the handler, the dependencies, the access this calculator requests, and — under `inputs` / `outputs` — the fields your handler reads and writes. |
| `src/calculator.py` | The handler. The implementation may span as many files as you like; `handler` names one exported symbol, not one source file. |
| `pyproject.toml` | Dependencies, including the SDK index. |
| `uv.lock` | The resolved dependency lock. **Generated — never edited by hand. Commit it.** |
| `fixtures/inputs.jsonl` | Sample rows for a local run, generated from the declared `inputs`. |
| `fixtures/references/` | Offline copies of declared reference datasets. |
| `tests/` | Your tests. They run locally, with no container and no platform connection. |
| `.vscode/` / `.run/` | VS Code and PyCharm seeds for Test and Run. |

## Getting started

```bash
# 1. Install uv (https://docs.astral.sh/uv/) if you do not already have it
uv sync                          # install dependencies and generate uv.lock
uv run riskfoundry login     # connects this laptop to the platform
uv run riskfoundry calc run --manifest calculator.yaml --input fixtures/inputs.jsonl
uv run riskfoundry test
uv lock                          # after every pyproject.toml change; commit the result
git push                         # then Publish from the platform UI
```

**`uv run` is not optional.** `uv sync` installs `riskfoundry` into this project's
`.venv`, and nothing puts that directory on your `PATH`, so a bare `riskfoundry` is
*command not found*. `uv run` resolves the project environment from the current directory.
To drop the prefix, activate the environment for your shell instead:
`.venv\Scripts\Activate.ps1` on Windows, `source .venv/bin/activate` elsewhere.

`uv.lock` must exist and be populated before this calculator can be published: an unlocked dependency
set would make a published revision non-reproducible. Run `uv lock` after every change to
`pyproject.toml`, and commit the result.

## The field names your handler uses

`calculator.yaml` declares them, under `inputs` and `outputs`:

```yaml
inputs:
  - name: income
    type: decimal
outputs:
  - name: score
    type: decimal
```

Those names are the contract. They are what arrives on each record, what you write back, and what the
platform checks its own mapping against when you publish — a mismatch is refused by name and by type,
with the differing fields listed, instead of failing later as a `KeyError` inside the container.

They are **not** the names a business user sees. On the platform each of your fields is mapped onto a
data item that keeps its own display name, so *Gross Annual Income* can be `income` here. Renaming the
data item does not touch your code.

A fresh scaffold declares `income` and `score` as a worked placeholder, so it runs end to end before
you have changed anything. To replace them with your model's real fields, declare and map them on the
platform, then press **Regenerate sample data** on the calculator's Source tab. That rewrites the two
blocks and `fixtures/inputs.jsonl` to match the mapping and commits the result to your branch; pull
it and carry on.

From the laptop, once you are logged in:

```bash
uv run riskfoundry calc sync --pull
```

Regenerate on the platform does the same and commits the result to your branch. Types are the
wire's own, so a platform Number is `decimal` here — never `integer`, which is accepted only on an
output where a handler returning a plain `int` is being helpful.

Nothing in this repository is a credential, a server URL, or a profile. Those live in your user
config directory (`%APPDATA%\riskfoundry` on Windows, `~/.config/riskfoundry` elsewhere),
created with permissions only your account can read.

A local run executes **your** code on **your** machine under **your** account. It is not sandboxed,
and nothing it produces is a published revision.

## Writing the handler

```python
def calculate(context, records):
    for record in records:
        yield {"recordId": record.id, "values": {"score": 0}}
```

Three rules the platform relies on:

- **Stream, don't collect.** Iterate `records` once and yield as you go. Materializing the whole input
  defeats the streaming execution the platform is built around, and large datasets will exhaust the
  memory your calculator is allowed.
- **Correlate by `recordId`, not by position.** Output may be emitted in any order; nothing is
  reordered on your behalf.
- **`print()` is safe.** Anything your code writes to stdout or stderr is captured as run logs, not as
  protocol output. It may contain data from the dataset under calculation, so it is treated as
  sensitive and truncated.
