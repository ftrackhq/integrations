# Connect publisher widget

## Building

### Preparations

Update release notes.

Set version in `pyproject.toml` (for this migration stream: `26.3.0.dev0`).

Bump the connect plugin version in integrations/projects/connect-publisher-widget/connect-plugin/__version__.py

Tag and push to SCM

### CI build

See Monorepo build CI


### Manual build

Build with uv:

```bash
  cd integrations/projects/connect-publisher-widget
  uv build
```

Build Connect plugin:

```bash
  cd integrations
  uv run python tools/build.py build_connect_plugin projects/connect-publisher-widget
```

If the build fails and publisher widget is using beta or experimental dependencies published to Test PyPi, use the `--testpypi` flag 
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
