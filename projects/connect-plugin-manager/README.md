# ftrack connect plugin manager

Documentation: [https://ftrackhq.github.io/integrations/projects/connect-plugin-manager/](https://ftrackhq.github.io/integrations/projects/connect-plugin-manager/)


## Building

### Preparations

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

Bump the connect plugin version in integrations/projects/connect-plugin-manager/connect-plugin/__version__.py

Tag and push to SCM

### CI build

See Monorepo build CI


### Manual build

Install development dependencies:

```bash
  cd integrations/projects/connect-plugin-manager
  poetry install --with documentation
```

Build with Poetry:

```bash
  cd integrations/projects/connect-plugin-manager
  poetry build
```

Build Connect plugin:


```bash
  cd integrations
  python tools/build.py build_connect_plugin projects/connect-plugin-manager
```

If the build fails and action launcher widget is using beta or experimental dependencies published to Test PyPi, use the `--testpypi` flag 
to build the plugin.


### Build documentation


Install development dependencies:

```bash
  poetry install --with documentation
```

Build documentation:

```bash
    poetry run sphinx-build -b html doc dist/doc
```
