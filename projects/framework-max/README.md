# ftrack Max integration

Community owned 3ds Max integration for ftrack.

# Documentation

## Building

### Preparations


1. Install Poetry

2. Create a Python 3.11 virtual environment.

3. Activate the virtual environment. 

4. If any dependent libraries updated, make sure to release them to PyPi prior to building the plugin.

5. Update release notes.

6. Set or bump version in pyproject.toml:

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

7. Bump the connect plugin version in integrations/projects/framework-max/connect-plugin/__version__.py

8. Tag and push to SCM


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
    python tools/build.py  --include_resources resource/bootstrap build_connect_plugin projects/framework-max
```

If the build fails and Max is using beta or experimental dependencies published to Test PyPi, use the `--testpypi` flag 
to build the plugin.

To build from source, not involving PyPi, use the `--from_source` flag.


## Installing

### Connect plugin
Copy the resulting dist/ftrack-framework-max-<version> folder to your connect plugin folder.
