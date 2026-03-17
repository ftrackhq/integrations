# Qt Style

This is the ftrack integrations qt-style library.
All style and resource files for qt used in the ftrack integrations products should be found here.

### Manual build

From `libs/qt-style`, build wheel artifacts and regenerate shared css resources:

```bash
  uv build
  uv run --with-requirements ../../tools/requirements-connect.txt python ../../tools/build.py build_qt_resources --css_only .
```
