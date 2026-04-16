# Qt Style

This is the ftrack integrations qt-style library.
All style and resource files for qt used in the ftrack integrations products should be found here.

### Preparations

Create and activate a project-local virtual environment:

```bash
cd libs/qt-style
uv venv .venv
source .venv/bin/activate
```

### Manual build

From `libs/qt-style`, build wheel artifacts and regenerate shared css and Qt resources:

```bash
  uv build
  uv run --with-requirements ../../tools/requirements-connect.txt python ../../tools/build.py --style_path ../../resource/style --output_path source/ftrack_qt_style/resource.py --pyside_version 6 build_qt_resources .
```
