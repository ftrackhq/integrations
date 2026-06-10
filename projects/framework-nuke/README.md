# Framework Nuke integration

Community owned Nuke integration for ftrack.

## Building

### Preparations


Install uv.

Create and activate a project-local virtual environment:

```bash
cd projects/framework-nuke
uv venv .venv
source .venv/bin/activate
```

Update release notes.

Set version in `pyproject.toml` (use semantic versioning, for example `MAJOR.MINOR.PATCH` or prerelease `MAJOR.MINOR.PATCHrcN`).

Bump the connect plugin version in projects/framework-nuke/connect-plugin/__version__.py

Tag and push to SCM


### CI build

See Monorepo build CI


### Manual build

Build with uv:

```bash
    uv build
```

#### Rebuilding Qt resources (styles)

The Qt stylesheets and icons used by the Nuke UI live in the `ftrack-qt-style` library
(`libs/qt-style`). They are pre-compiled into `libs/qt-style/source/ftrack_qt_style/resource.py`
from the SCSS / images under `resource/style/` at the repo root.

If you've made changes to the shared styles under `resource/style/sass/` (or pulled changes
that touch them), regenerate the Qt resources before building the Connect plugin, otherwise
the bundled plugin will ship with stale styles:

```bash
    cd libs/qt-style
    uv build
    uv run --with-requirements ../../tools/requirements-connect.txt python ../../tools/build.py \
        --style_path ../../resource/style \
        --output_path source/ftrack_qt_style/resource.py \
        --pyside_version 6 \
        build_qt_resources .
```

This recompiles `resource/style/style_dark.css` / `style_light.css` from SCSS and writes a
fresh `resource.py`. The framework-nuke `pyproject.toml` references `ftrack-qt-style` via a
local path in `[tool.uv.sources]`, so the next Connect plugin build will pick up the
freshly built resources automatically.

#### Build Connect plugin


```bash
    cd projects/framework-nuke
    uv run python ../../tools/build.py --include_resources resource/bootstrap build_connect_plugin .
```

If the build fails and Nuke is using beta or experimental dependencies published to Test PyPi, use the `--testpypi` flag 
to build the plugin.

To build from source, not involving PyPi, use the `--from_source` flag. Note that the default
build already resolves the in-repo `ftrack-*` libs from local paths via `[tool.uv.sources]`,
so `--from_source` is only needed when you intentionally want to bypass that resolution.


### Build documentation


Install documentation dependencies:

```bash
    uv sync --extra documentation
```

Build documentation:

```bash
    uv run sphinx-build -b html doc dist/doc
```

## Installing

### Connect plugin
Copy the resulting dist/ftrack-framework-nuke-<version> folder to your connect plugin folder.
