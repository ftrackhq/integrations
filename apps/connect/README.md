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

### Manual Build
1. Create and activate a virtual environment:
- Create a Python 3.10 virtual environment.
- Activate the virtual environment. 

2. Build resources:
```bash
cd integrations
pip install -r tools/requirements-connect.txt
python tools/build.py --style_path resource --output_path source/ftrack_connect/ui/resource.py --pyside_version 6 build_qt_resources apps/connect
```
3. Go to the Connect package within monorepo:

```bash
    cd integrations/apps/connect
```

4. Update dependencies:

```bash
    poetry update
```
5. Test connect and install it from sources (Optional)

```bash
    poetry install --with dev --sync
```
   1. Start connect:

   ```bash
       python -m ftrack_connect
   ```
6. Build Connect wheel (Optional)

```bash
  poetry build
```

7. Generate distributible connect installer

```bash
  poetry install --with installer --sync
  poetry run ftrack-connect-installer --codesign true
```
Note:: If --codesign is true, please make sure you have followed all the instructions from:

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

