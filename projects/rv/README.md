# Rv integration

ftrack connect rv integration.

## Building

### Preparations

Update release notes.

Set version in `pyproject.toml` (use semantic versioning, for example `MAJOR.MINOR.PATCH` or prerelease `MAJOR.MINOR.PATCHrcN`).

Bump the connect plugin version in projects/rv/connect-plugin/__version__.py

Tag and push to SCM


### CI build

See Monorepo build CI


### Manual build

Build with uv:
     
```bash
    uv build --active
```

Create the RV plugin, it will read the version number from pyproject.toml:

```bash
  cd projects/rv
  uv run --active python ../../tools/build.py --output_path . build_rvpkg .
```


Build the Connect plugin from the project folder:

```bash
  cd projects/rv
  uv run --active python ../../tools/build.py --include_assets ./ftrack-26.3.rvpkg build_connect_plugin .
```


If the build fails and RV is using beta or experimental dependencies published to Test PyPi, use the `--testpypi` flag 
to build the plugin.

```bash
  cd projects/rv
  uv run --active python ../../tools/build.py --testpypi --include_assets ./ftrack-26.3.rvpkg build_connect_plugin .
```

The Connect plugin will be output to the dist/ folder.
