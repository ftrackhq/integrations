# Framework Blender integration

Community owned Blender integration for ftrack.

## Building

### Preparations


Install uv

Create and activate a project-local virtual environment:

```bash
cd projects/framework-blender
uv venv .venv
source .venv/bin/activate
```

Update release notes.

Set version in `pyproject.toml` (use semantic versioning, for example `MAJOR.MINOR.PATCH` or prerelease `MAJOR.MINOR.PATCHrcN`).

Bump the connect plugin version in projects/framework-blender/connect-plugin/__version__.py

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
    cd projects/framework-blender
    uv run python ../../tools/build.py --include_resources resource/bootstrap build_connect_plugin .
```

If the build fails and Blender is using beta or experimental dependencies published to Test PyPi, use the `--testpypi` flag 
to build the plugin.

To build from source, not involving PyPi, use the `--from_source` flag.


## Installing

### Connect plugin
Copy the resulting dist/ftrack-framework-blender-<version> folder to your connect plugin folder.
