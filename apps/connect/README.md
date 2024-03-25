# ftrack Connect

Core for ftrack connect providing main service that enhances
functionality of the ftrack web server and also provides standalone
applications for workflows including logging time and publishing assets.

## Documentation

Full documentation, including installation and setup guides, can be
found at <https://developer.ftrack.com/integrating-pipelines/connect/>

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

### Test connect from sources
1. Go to the Connect package within monorepo:

```bash
    cd integrations/apps/connect
```

2. Create and activate a virtual environment:
- Create a Python 3.7 virtual environment. If you're using an Apple Silicon chip, follow the instructions in the [How to install compatible PySide2 on Silicon based Mac](../../README.md#how-to-install-compatible-pyside2-on-silicon-based-mac) section.
- Activate the virtual environment. 

3. Update dependencies:

```bash
    poetry update
```

4. Install dependencies:

```bash
    poetry install --extras ftrack-libs framework-libs # If you want to manually use ftrack-libraries from sources, don't install extras and manually install them following its own readme file.
```
   1. To install framework-libs from sources:
   ```bash
       cd ../../libs/framework-core
       poetry install
   ```

   2. To install ftrack-libs from sources:
   ```bash
       cd ../../libs/utils
       poetry install
   ```

5. Start connect:

```bash
    python -m ftrack_connect
```

### Manual build

1. Go to the Connect package within monorepo:

```bash
    cd integrations/apps/connect
```

2. Create and activate a virtual environment:
- Create a Python 3.7 virtual environment. If you're using an Apple Silicon chip, follow the instructions in the [How to install compatible PySide2 on Silicon based Mac](../../README.md#how-to-install-compatible-pyside2-on-silicon-based-mac) section.
- Activate the virtual environment. 

3. Update dependencies:

```bash
    poetry update
```

4. Install dependencies:

```bash
    poetry install --extras ftrack-libs framework-libs
```

5. Build the QT resources

```bash
cd ../..
pip install -r tools/requirements.txt
python tools/build.py --style_path resource --output_path source/ftrack_connect/ui/resource.py build_qt_resources apps/connect
cd integrations/apps/connect
```

7. Build with Poetry:

```bash
  poetry build
```
### Install wheel

```bash
  pip install dist/ftrack-connect-<version>.whl
```

### Build documentation

1. Install documentation dependencies:

```bash
  poetry install --only documentation
```

2. Build documentation:

```bash
    poetry run sphinx-build -b html doc dist/doc
```

## Publish to PyPi

This is performed by the CI, to publish to PyPi test - follow the instructions in integrations README.md at root level of 
repository.

