# ftrack Houdini integration

Community owned Houdini integration for ftrack.

# Documentation

## Building

### Preparations


1. Install uv

2. Create a Python `>=3.13,<3.14` virtual environment.

3. Activate the virtual environment. 

4. If any dependent libraries updated, make sure to release them to PyPi prior to building the plugin.

5. Update release notes.

6. Set version in `pyproject.toml` (use semantic versioning, for example `MAJOR.MINOR.PATCH` or prerelease `MAJOR.MINOR.PATCHrcN`).

7. If dependencies updated, update the uv lock file and validate the change.

```bash
    uv lock --active
```

8. Tag and push to SCM



### CI build

See Monorepo build CI


### Manual build

Build with uv:

```bash
    uv build --active
```

Build Connect plugin:


```bash
    cd projects/framework-houdini
    uv run --active python ../../tools/build.py --include_resources resource/bootstrap build_connect_plugin .
```

If the build fails and Houdini is using beta or experimental dependencies published to Test PyPi, use the `--testpypi` flag 
to build the plugin.

To build from source, not involving PyPi, use the `--from_source` flag.


## Installing

### Connect plugin
Copy the resulting dist/ftrack-framework-houdini-<version> folder to your connect plugin folder.
