# Framework Blender integration

Community owned Blender integration for ftrack.

## Building

### Preparations


Install Poetry

Create a Python 3.11 virtual environment.

Activate the virtual environment. 

Update release notes.

Set or bump version in pyproject.toml:

```bash
    poetry version prerelease
```
or:
```bash
    poetry version patch
```
or:
```bash
    poetry version minor
```
or:
```bash
    poetry version major
```

Bump the connect plugin version in integrations/projects/framework-blender/connect-plugin/__version__.py

Tag and push to SCM


### CI build

See Monorepo build CI


### Manual build

Build with Poetry:

```bash
    poetry build
```

Build Connect plugin:


```bash
    cd integrations
    python tools/build.py --include_resources resource/bootstrap build_connect_plugin projects/framework-blender
```

If the build fails and Blender is using beta or experimental dependencies published to Test PyPi, use the `--testpypi` flag 
to build the plugin.

To build from source, not involving PyPi, use the `--from_source` flag.


## Installing

### Connect plugin
Copy the resulting dist/ftrack-framework-blender-<version> folder to your connect plugin folder.
