# ftrack-connect

Core for ftrack connect providing main service that enhances
functionality of the ftrack web server and also provides standalone
applications for workflows including logging time and publishing assets.

## Documentation

Full documentation, including installation and setup guides, can be
found at <http://ftrack-connect.rtd.ftrack.com/en/latest/>

## Building

### CI build

See Monorepo build CI


### Manual build

Go to the Connect package within monorepo:

```bash
    cd integrations/apps/connect
```

Install development dependencies:

```bash
  poetry install --with documentation
```

Go to the root of the Connect package within monorepo:

```bash
    cd integrations
```

Build the QT resources

```bash
python tools/build.py --style_path resource --output_path source/ftrack_connect/ui/resource.py build_qt_resources apps/connect
```

Build with Poetry:

```bash
  poetry build
```


### Build documentation

Install development dependencies:

```bash
  poetry install --with documentation
```

Build documentation:

```bash
    poetry run sphinx-build -b html doc dist/doc
```

## Publish to PyPi

This is performed by the CI, to publish to PyPi test - follow the instructions in integrations README.md at root level of 
repository.

