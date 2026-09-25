# dp-rest

REST api dp

A RiskFoundry code data provider. Its entry point is `build` in `src/provider.py`, as
declared by `handler` in `provider.yaml`.

A provider populates a dataset. A calculator consumes a dataset that is already populated and does not
know how it got that way — so a calculator never imports a provider, and the two are versioned and
published separately.

Local runs are for development. The container run is the truth: the builder image remains the
publish gate, local runs enforce limits only with `--limits`, they do not isolate the network, and
they may run on a different Python patch level than the image (`riskfoundry doctor` warns).

## Layout

| Path | What it is |
|---|---|
| `provider.yaml` | The manifest. Declares the runtime, the handler, where this provider may run, the sources it requests and the access it requests. |
| `src/provider.py` | The handler. The implementation may span as many files as you like; `handler` names one exported symbol, not one source file. |
| `pyproject.toml` | Dependencies, including the SDK index. |
| `uv.lock` | The resolved dependency lock. **Generated — never edited by hand. Commit it.** |
| `tests/` | Your tests. They run locally, with no container and no platform connection. |
| `.vscode/` / `.run/` | VS Code and PyCharm seeds for Test and Run provider. |

## Getting started

```bash
# 1. Install uv (https://docs.astral.sh/uv/) if you do not already have it
uv sync                          # install dependencies and generate uv.lock
uv run riskfoundry login     # connects this laptop to the platform
uv run riskfoundry provider run --manifest provider.yaml --print 5
uv run riskfoundry test
uv lock                          # after every pyproject.toml change; commit the result
git push                         # then Publish from the platform UI
```

**`uv run` is not optional.** `uv sync` installs `riskfoundry` into this project's
`.venv`, and nothing puts that directory on your `PATH`, so a bare `riskfoundry` is
*command not found*. `uv run` resolves the project environment from the current directory.
To drop the prefix, activate the environment for your shell instead:
`.venv\Scripts\Activate.ps1` on Windows, `source .venv/bin/activate` elsewhere.

`uv.lock` must exist and be populated before this provider can be published: an unlocked dependency
set would make a published revision non-reproducible. Run `uv lock` after every change to
`pyproject.toml`, and commit the result.

Nothing in this repository is a credential, a server URL, or a profile. Those live in your user
config directory (`%APPDATA%\riskfoundry` on Windows, `~/.config/riskfoundry` elsewhere),
created with permissions only your account can read.

A local run executes **your** code on **your** machine under **your** account. It is not sandboxed,
and nothing it produces is a published revision.

## Writing the handler

```python
def build(context):
    for row in extract(context):
        yield {"recordId": row.key, "values": {"amount": row.amount}}
```

Four rules the platform relies on:

- **Stream, don't collect.** Yield each record as you obtain it. Building the whole result in a list
  first defeats the streaming publication the platform is built around, and a large extract will
  exhaust the memory your provider is allowed.
- **`recordId` is a stable identity**, not a row number. Re-running the provider against unchanged
  source data should produce the same identities.
- **Name profiles, never connections.** `sources` in the manifest names a profile an administrator
  configured. Credentials never reach your code, and a connection string in this repository is a
  secret in version control.
- **`print()` is safe.** Anything your code writes to stdout or stderr is captured as run logs, not as
  protocol output. It may contain data from the source you extracted, so it is treated as sensitive
  and truncated.

## Where it runs

`execution` in the manifest declares where this provider may run:

| Mode | Meaning |
|---|---|
| `local` | On a developer machine, against sources only that machine can reach. |
| `sandbox` | As a platform job, against sources the platform can reach. |
| `both` | Either, chosen per run. |

It is a statement about reachability, not a permission: what a provider is allowed to touch is decided
by the platform at run time, never by this file.
