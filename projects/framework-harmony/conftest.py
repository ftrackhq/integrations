# :coding: utf-8
# :copyright: Copyright (c) 2026 ftrack

# Workstation-only DCC integration tests. They need dcc-test-harness
# (installed via this project's `test` extra); when pytest runs from
# the repo root (CI) that env is absent - skip collection entirely
# instead of erroring at import. Run them from this directory:
#     uv sync --extra ftrack-libs --extra framework-libs --extra test
#     uv run pytest tests/
try:
    import dcc_test_harness  # noqa: F401
except ModuleNotFoundError as error:
    if error.name != "dcc_test_harness":
        raise
    collect_ignore = ["tests"]
