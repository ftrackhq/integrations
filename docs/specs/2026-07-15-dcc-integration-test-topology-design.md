# DCC integration test topology: colocate, guard root collection, one job per env

Status: implemented

This records where DCC integration tests live and how CI treats them, so
future integrations (Maya, Maya-Deadline, …) follow the same shape.

## Problem

`push-main-test.yml` runs `pytest` from the repo root in a venv synced
with the root `pyproject.toml` extras. Root pytest has no `testpaths`, so
it recurses into every `tests/` directory it finds. The Harmony suite
(`projects/framework-harmony/tests/`) and the harness's own suite
(`libs/dcc-test-harness/tests/`) both `import dcc_test_harness` at module
level — a package that is **not** on the root `pythonpath` and **not**
installed in the root venv. Without a guard that is a
`ModuleNotFoundError` at *collection* time, before any `skipif` /
`pytest.skip` can fire.

These suites are **workstation-only integration tests**: they launch a
real DCC and exist to give developers and AI agents a fast automated
dev/test loop (`edit source → uv run pytest tests/` in one checkout).
The question this doc settles is *where they live* and *how CI treats
them*.

## Two test homes in this monorepo

There are deliberately two categories, split by how a component is wired:

1. **Flat pythonpath libs** — `constants`, `utils`, `framework-core`,
   `framework-qt`, `qt`, `qt-style`. Their `source/` dirs are listed in
   the root `[tool.pytest.ini_options] pythonpath`, they have no `tests/`
   of their own, and they are exercised centrally by the repo-root
   `tests/` suite (which imports them directly). One root venv holds all
   their deps; the root CI job runs them.

2. **Self-contained packages** — `libs/dcc-test-harness` and every
   `projects/<integration>`. Each carries its own `pyproject.toml` +
   `uv.lock` + venv and is consumed elsewhere as a path dependency. Each
   **owns its own `tests/`** and is tested by running pytest *from its
   own directory*, where its extras (and the harness path source) are
   installed.

`dcc-test-harness` is squarely category 2: it is a self-contained package
(`pyproject`, `uv.lock`, `README`, self-tests) that also exists as a
standalone repo (`ftrackhq/dcc-test-harness`). Its dependency closure
includes `ftrack-connect` (via a path source), which the flat-lib
pythonpath mechanism cannot supply.

## Decision

**Colocate each integration's tests with the code under test; keep root
CI blind to them via a collection guard; give the harness's own headless
unit suite a dedicated CI job.**

### 1. Colocation (not a shared external test repo)

Tests stay in `projects/<integration>/tests/` (and
`libs/dcc-test-harness/tests/` for the harness's self-tests). Reasons:

- **Tests version with the code under test.** The Harmony tests encode
  intimate integration details (RPC handshake, TCP role flip, bootstrap
  scene, watchdog PID semantics — see the scene-switch design doc). A
  source change and its test change belong in one commit/PR. A separate
  test repo means cross-repo drift and non-atomic reviews.
- **The AI dev/test loop favours colocation.** Edit source → `uv run
  pytest tests/` from the project dir → repeat, in ONE checkout. A
  separate repo forces two checkouts with matching branches and sibling
  path deps.

### 2. Collection guard (the root-CI fix)

Each self-contained package with a `tests/` dir carries a `conftest.py`
at its **package root** with:

```python
try:
    import dcc_test_harness  # noqa: F401
except ModuleNotFoundError as error:
    if error.name != "dcc_test_harness":
        raise
    collect_ignore = ["tests"]
```

Catching `ModuleNotFoundError` (not the broader `ImportError`) and
re-raising when it names a different module keeps a real broken import
inside `dcc_test_harness` from being silently swallowed as "harness
absent."

When pytest runs from the package's own venv the import succeeds and the
suite collects normally (the guard is a no-op). When pytest runs from the
repo root (CI, or a repo-root `pytest`) the package is absent, so the
`tests/` dir is dropped from collection instead of erroring. The
in-suite capability skips (credentials `skipif`, `pytest.skip` on launch
`FileNotFoundError`) remain the gating **when actually run on a
workstation**.

This is the pattern to copy for every future DCC integration.

### 3. One CI job per environment

- The existing root job (`unit-test-pytest`) covers the flat pythonpath
  libs via the root `tests/` suite. Unchanged.
- A small `harness-unit-pytest` job runs the harness's own
  **pure-unit, headless** protocol suite (`tests/test_protocol.py`) from
  `libs/dcc-test-harness` (`uv sync --extra test && uv run pytest`).
  Without it that suite would get zero CI coverage — the guard hides it
  from the root run. It is the harness's equivalent of what the root
  suite does for the flat libs.
- **No CI job for the workstation-only suites** (Harmony, and future
  DCC integrations). Running them in CI would only print skips; they are
  covered on developer/agent workstations.

## Alternative considered and rejected: move harness unit tests to root `tests/`

Technically cheap — `test_protocol.py`'s import chain (`_protocol`,
`client`, `exceptions`) is pure stdlib, so it could run with only
`libs/dcc-test-harness/source` added to the root `pythonpath`, no new
root deps. Rejected because:

- The Harmony integration suite **cannot** move regardless (sibling
  helper modules, the harness's `--dcc-connect-plugin` plugin options,
  launching a real Harmony, versioning-with-code). So the
  colocated+guarded model must exist anyway — moving only the harness
  unit test doesn't unify anything, it just makes the harness the one
  package whose tests don't sit next to it.
- It splits a vendored, self-contained package's self-test from the
  package, hurting a future re-sync / re-extraction and breaking the
  "code and its tests version together" principle for exactly the
  component that was extracted to stand alone.

Net: the "all CI unit tests in one place" goal is unreachable (the
workstation suites break it by nature), and the shape it would land on is
less consistent, not more.

## Current gaps

- The Maya integration suite still lives in the external harness repo's
  `tests/maya/` rather than `projects/framework-maya/tests/`. It is
  effectively framework-maya's integration suite, not harness infra, and
  the colocated+guarded model above is where it belongs.
- `framework-maya-deadline` consumes `dcc-test-harness` from a sibling
  checkout rather than the in-repo `../../libs/dcc-test-harness`, and does
  not yet carry the collection guard.
