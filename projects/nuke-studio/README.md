# ftrack connect NUKE STUDIO

ftrack integration with NUKE STUDIO.

Documentation: [https://ftrackhq.github.io/integrations/projects/nuke-studio/](https://ftrackhq.github.io/integrations/project/nuke-studio/)

## Building

### CI build

See Monorepo build CI


### Manual build

Go to the root of the RV package within monorepo:

```bash
    cd integrations
```


Build the QT resources

```bash
python tools/build.py --style_path resource --output_path source/ftrack_nuke_studio/resource.py build_qt_resources projects/nuke-studio
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

