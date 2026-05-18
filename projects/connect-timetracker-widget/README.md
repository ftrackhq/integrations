# Connect timetracker widget

## Building

### Preparations

Install uv.

Create and activate a project-local virtual environment:

```bash
cd projects/connect-timetracker-widget
uv venv .venv
source .venv/bin/activate
```

Update release notes.

Set version in `pyproject.toml` (use semantic versioning, for example `MAJOR.MINOR.PATCH` or prerelease `MAJOR.MINOR.PATCHrcN`).

Bump the connect plugin version in projects/connect-timetracker-widget/connect-plugin/__version__.py

Tag and push to SCM

### CI build

See Monorepo build CI


### Manual build

Build with uv:

```bash
  cd projects/connect-timetracker-widget
  uv build
```

Build Connect plugin:

```bash
  cd projects/connect-timetracker-widget
  uv run python ../../tools/build.py build_connect_plugin .
```

If the build fails and timetracker widget is using beta or experimental dependencies published to Test PyPi, use the `--testpypi` flag 
to build the plugin.


### Build documentation


Install documentation dependencies:

```bash
  uv sync --extra documentation
```

Build documentation:

```bash
    uv run sphinx-build -b html doc dist/doc
```
