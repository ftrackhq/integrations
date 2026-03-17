# Framework Blender integration

Community owned Blender integration for ftrack.

## Building

### Preparations


Install uv

Create a Python `>=3.13,<3.14` virtual environment.

Activate the virtual environment. 

Update release notes.

Set version in `pyproject.toml` (for this migration stream: `26.3.0.dev0`).

Bump the connect plugin version in integrations/projects/framework-blender/connect-plugin/__version__.py

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
