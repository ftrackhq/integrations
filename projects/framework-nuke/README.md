# Framework Nuke integration

Community owned Nuke integration for ftrack.

## Building

### Preparations


Install uv.

Create and activate a project-local virtual environment:

```bash
cd projects/framework-nuke
uv venv .venv
source .venv/bin/activate
```

Update release notes.

Set version in `pyproject.toml` (use semantic versioning, for example `MAJOR.MINOR.PATCH` or prerelease `MAJOR.MINOR.PATCHrcN`).

Bump the connect plugin version in projects/framework-nuke/connect-plugin/__version__.py

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
    cd projects/framework-nuke
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
