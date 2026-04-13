# Framework Photoshop integration

Community owned Photoshop integration for ftrack.

## Building

### Preparations


1. Install uv.

2. Create a Python `>=3.13,<3.14` virtual environment.

3. Activate the virtual environment. 

4. If any dependent libraries updated, make sure to release them to PyPi prior to building the plugin.

5. Update release notes.

6. Set version in `pyproject.toml` (use semantic versioning, for example `MAJOR.MINOR.PATCH` or prerelease `MAJOR.MINOR.PATCHrcN`).

7. If dependencies updated, update the uv lock file. Remember to properly validate/test the change of dependencies.

```bash
    uv lock
```

8. Tag and push to SCM


### CI build

See Monorepo build CI


### Manual build

1. Build with uv

```bash
    uv build
```

2. Build Connect plugin from wheel and the locked dependencies using Monorepo custom toolset:

```bash
    cd projects/framework-photoshop
    uv run python ../../tools/build.py build_connect_plugin .
```

If the build fails and Photoshop is using beta or experimental dependencies published to Test PyPi, use the `--testpypi` flag 
to build the plugin.

To build from source, not involving PyPi, use the `--from_source` flag.


# Development


## Installing

### Connect plugin
Copy the resulting dist/ftrack-framework-photoshop-<version> folder to your connect plugin folder.


## UXP plugin

Build UXP artifact:

```bash
    cd projects/framework-photoshop
    uv run python ../../tools/build.py --remove_intermediate_folder build_uxp .
```

The output artifact is placed in `projects/framework-photoshop/dist/` as:

- `ftrack-framework-photoshop-<version>.ccx`

### UXP local testing

1. Build the UXP artifact.
2. Unzip it locally.
3. Open Adobe UXP Developer Tool.
4. Add plugin from the unzipped folder that contains `manifest.json`.
5. Launch Photoshop from ftrack Connect so bootstrap files are generated.
6. Open panel `ftrack` in Photoshop and validate connection.
