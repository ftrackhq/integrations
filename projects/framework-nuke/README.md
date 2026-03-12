# Framework Nuke integration

Community owned Nuke integration for ftrack.

## Building

### Preparations


Install uv and create a Python `>=3.13,<3.14` virtual environment.

Update release notes.

Set version in `pyproject.toml` (for this migration stream: `26.3.0.dev0`).

Bump the connect plugin version in integrations/projects/framework-nuke/connect-plugin/__version__.py

Tag and push to SCM


### CI build

See Monorepo build CI


### Manual build

Build with uv:

```bash
    uv build
```

Build Connect plugin:


```bash
    cd integrations/projects/framework-nuke
    uv run python ../../tools/build.py --include_resources resource/bootstrap build_connect_plugin .
```

If the build fails and Nuke is using beta or experimental dependencies published to Test PyPi, use the `--testpypi` flag 
to build the plugin.

To build from source, not involving PyPi, use the `--from_source` flag.


### Build documentation


Install documentation dependencies:

```bash
    uv sync --extra documentation
```

Build documentation:

```bash
    uv run sphinx-build -b html doc dist/doc
```

## Installing

### Connect plugin
Copy the resulting dist/ftrack-framework-nuke-<version> folder to your connect plugin folder.
