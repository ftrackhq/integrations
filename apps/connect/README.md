# ftrack-connect

Core for ftrack connect providing main service that enhances
functionality of the ftrack web server and also provides standalone
applications for workflows including logging time and publishing assets.

## Documentation

Full documentation, including installation and setup guides, can be
found at <http://ftrack-connect.rtd.ftrack.com/en/latest/>

## Building

### Preparations

1. Clone the public repository:

    $ git clone https://github.com/ftrackhq/integrations.git

2. Update release notes.

3. Install Poetry (https://python-poetry.org/docs/#installation)

4. Set or bump version in pyproject.toml:

```bash
   cd integrations/apps/connect
```


```bash
    poetry version prerelease
```
or:
```bash
    poetry version patch
```
or:
```bash
    poetry version minor
```
or:
```bash
    poetry version major
```

5. Tag and push to SCM


### CI build

See Monorepo build CI


### Manual build

1. Go to the Connect package within monorepo:

```bash
    cd integrations/apps/connect
```

2. Install development dependencies:

```bash
    poetry install --with documentation
```

3. Go to the root of the Connect package within monorepo:

```bash
    cd integrations
```

4. Activate a virtual environment:

```bash
    poetry shell
```

5. Build the QT resources

```bash
python tools/build.py --style_path resource --output_path source/ftrack_connect/ui/resource.py build_qt_resources apps/connect
```

6. Build with Poetry:

```bash
  poetry build
```

### Build documentation

1. Install development dependencies:

```bash
  poetry install --with documentation
```

2. Build documentation:

```bash
    poetry run sphinx-build -b html doc dist/doc
```

## Publish to PyPi

This is performed by the CI, to publish to PyPi test - follow the instructions in integrations README.md at root level of 
repository.

