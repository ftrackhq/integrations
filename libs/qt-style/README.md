# ftrack-style

Documentation: [https://ftrackhq.github.io/integrations/libs/qt-style/](https://ftrackhq.github.io/integrations/libs/qt-style/)

## Building


### CI build

See Monorepo build CI

### Manual build

Go to the root of the Monorepo and build the ftrack style resource.py:

```bash
  cd integrations
  pip install -r tools/requirements.txt
  python tools/build.py build_qt_resources libs/qt-style
```

Go to the root of the QT style package within monorepo:

```bash
    cd integrations/libs/qt-style
```

Build with Poetry:
    
```bash
    poetry build
```

See Monorepo documentation on how to publish the build to PyPi.

