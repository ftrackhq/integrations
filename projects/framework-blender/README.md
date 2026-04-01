# Framework Blender integration

Community owned Blender integration for ftrack.

## Building

### Preparations


Install uv

Create a Python `>=3.13,<3.14` virtual environment.

Activate the virtual environment. 

Update release notes.

Set version in `pyproject.toml` (use semantic versioning, for example `MAJOR.MINOR.PATCH` or prerelease `MAJOR.MINOR.PATCHrcN`).

Bump the connect plugin version in projects/framework-blender/connect-plugin/__version__.py

Tag and push to SCM


### CI build

See Monorepo build CI


### Manual build

Build with uv:

```bash
    uv build --active
```

Build Connect plugin:


```bash
    cd projects/framework-blender
    uv run --active python ../../tools/build.py --include_resources resource/bootstrap build_connect_plugin .
```

If the build fails and Blender is using beta or experimental dependencies published to Test PyPi, use the `--testpypi` flag 
to build the plugin.

To build from source, not involving PyPi, use the `--from_source` flag.


## Installing

### Connect plugin
Copy the resulting dist/ftrack-framework-blender-<version> folder to your connect plugin folder.
