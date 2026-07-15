# :coding: utf-8
# :copyright: Copyright (c) 2026 ftrack

# Collection guard: whether dcc_test_harness is importable depends on
# the venv pytest was launched from, not on the source sitting next to
# this file (src layout - source/dcc_test_harness is only importable
# once installed). In this project's own venv the import succeeds and
# tests/ is collected; in the repo-root venv (CI runs pytest from the
# repo root) the package is not installed, and tests/test_protocol.py
# imports it at module level - so ignore tests/ there instead of
# failing collection. Run the tests from this directory:
#     uv sync --extra test
#     uv run pytest
try:
    import dcc_test_harness  # noqa: F401
except ModuleNotFoundError as error:
    if error.name != "dcc_test_harness":
        raise
    collect_ignore = ["tests"]
