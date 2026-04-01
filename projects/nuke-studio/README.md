# Nuke Studio integration

ftrack integration with NUKE STUDIO.

## Building

### Preparations

Update release notes.

Set version in `pyproject.toml` (use semantic versioning, for example `MAJOR.MINOR.PATCH` or prerelease `MAJOR.MINOR.PATCHrcN`).

Bump the connect plugin version in projects/nuke-studio/connect-plugin/__version__.py

Tag and push to SCM

### CI build

See Monorepo build CI


### Manual build

Install nuke dependencies:

```bash
  cd projects/nuke-studio
  uv sync
```

Build with uv:

```bash
  cd projects/nuke-studio
  uv build
```

Build Connect plugin:


```bash
  cd projects/nuke-studio
  uv run python ../../tools/build.py --include_resources resource/plugin,resource/application_hook build_connect_plugin .
```

If the build fails and Nuke Studio is using beta or experimental dependencies published to Test PyPi, use the `--testpypi` flag 
to build the plugin.


### Build documentation


Install documentation dependencies:

```bash
  uv sync --extra documentation
```

Build documentation:

```bash
    uv run sphinx-build -b html doc dist/doc
```


