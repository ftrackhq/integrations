# ftrack Harmony integration

Community owned Harmony integration for ftrack.

# Documentation

## Building

### Preparations


1. Install uv

2. Create and activate a project-local virtual environment:

```bash
cd projects/framework-harmony
uv venv .venv
source .venv/bin/activate
```

4. If any dependent libraries updated, make sure to release them to PyPi prior to building the plugin.

5. Update release notes.

6. Set version in `pyproject.toml` (use semantic versioning, for example `MAJOR.MINOR.PATCH` or prerelease `MAJOR.MINOR.PATCHrcN`).

7. Tag and push to SCM


### CI build

See Monorepo build CI


### Manual build

Build with uv:

```bash
    uv build
```

Build Connect plugin:

```bash
    cd projects/framework-harmony
    uv run python ../../tools/build.py --include_resources resource/bootstrap build_connect_plugin .
```

If the build fails and Harmony is using beta or experimental dependencies published to Test PyPi, use the `--testpypi` flag 
to build the plugin.

To build from source, not involving PyPi, use the `--from_source` flag.


## Installing

### Connect plugin
Copy the resulting dist/ftrack-framework-harmony-<version> folder to your connect plugin folder.
