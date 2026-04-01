# Connect publisher widget

## Building

### Preparations

Update release notes.

Set version in `pyproject.toml` (use semantic versioning, for example `MAJOR.MINOR.PATCH` or prerelease `MAJOR.MINOR.PATCHrcN`).

Bump the connect plugin version in projects/connect-publisher-widget/connect-plugin/__version__.py

Tag and push to SCM

### CI build

See Monorepo build CI


### Manual build

Build with uv:

```bash
  cd projects/connect-publisher-widget
  uv build --active
```

Build Connect plugin:

```bash
  cd projects/connect-publisher-widget
  uv run --active python ../../tools/build.py build_connect_plugin .
```

If the build fails and publisher widget is using beta or experimental dependencies published to Test PyPi, use the `--testpypi` flag 
to build the plugin.


### Build documentation


Install documentation dependencies:

```bash
  uv sync --active --extra documentation
```

Build documentation:

```bash
    uv run --active sphinx-build -b html doc dist/doc
```
