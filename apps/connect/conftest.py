# :coding: utf-8
# :copyright: Copyright (c) 2026 ftrack

# ftrack Connect's tests are workstation/self-contained-package tests: they
# import from `ftrack_connect`, which is only importable in this package's
# own venv (`uv sync` from apps/connect). The repo-root pytest run (CI's
# unit-test-pytest job) has no `testpaths` and recurses into every `tests/`
# directory it finds, including this one - but the root venv has no
# `ftrack_connect`, so collection would error before any skip could fire.
# Skip collecting `tests/` when `ftrack_connect` is absent.
#
# find_spec (not a real `import ftrack_connect`) is used deliberately:
# importing the package runs ftrack_connect/__init__.py, which does
# `import qtawesome` -> PySide6 and needs Qt system libs that only the
# connect-unit-pytest job provides. find_spec just locates the module
# without executing it.
import importlib.util

if importlib.util.find_spec("ftrack_connect") is None:
    collect_ignore = ["tests"]
