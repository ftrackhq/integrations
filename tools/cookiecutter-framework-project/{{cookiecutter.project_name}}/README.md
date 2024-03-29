# ftrack {{ cookiecutter.integration_name.capitalize() }} integration

Community owned {{ cookiecutter.integration_name.capitalize() }} integration for ftrack.

# Documentation

## Building

### Preparations


Install Poetry

Create a Python >=3.7, <3.12 virtual environment. If you're using an Apple Silicon chip, follow the instructions in the [How to install compatible PySide2 on Silicon based Mac](../../README.md#how-to-install-compatible-pyside2-on-silicon-based-mac) section. 

Activate the virtual environment. 

Update release notes.

Set or bump version in pyproject.toml:

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

Bump the connect plugin version in integrations/projects/framework-{{ cookiecutter.integration_name }}/connect-plugin/__version__.py

Tag and push to SCM


### CI build

See Monorepo build CI


### Manual build

Build with Poetry:

```bash
    poetry build
```

Build Connect plugin:


```bash
    cd integrations
    python tools/build.py  --include_resources resource/bootstrap build_connect_plugin projects/framework-{{ cookiecutter.integration_name }}
```

If the build fails and {{ cookiecutter.integration_name.capitalize() }} is using beta or experimental dependencies published to Test PyPi, use the `--testpypi` flag 
to build the plugin.

To build from source, not involving PyPi, use the `--from_source` flag.


### Build documentation


Install documentation dependencies:

```bash
    poetry install --only documentation
```

Build documentation:

```bash
    poetry run sphinx-build -b html doc dist/doc
```

## Installing

### Connect plugin
Copy the resulting dist/ftrack-framework-{{ cookiecutter.integration_name }}-<version> folder to your connect plugin folder.
