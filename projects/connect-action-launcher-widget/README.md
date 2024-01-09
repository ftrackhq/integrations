# ftrack connect action launcher widget

Documentation: [https://ftrackhq.github.io/integrations/projects/connect-action-launcher-widget/](https://ftrackhq.github.io/integrations/projects/connect-action-launcher-widget/)

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

Bump the connect plugin version in integrations/projects/connect-action-launcher-widget/connect-plugin/__version__.py

Tag and push to SCM

### CI build

See Monorepo build CI


### Manual build

Build with Poetry:

```bash
  cd integrations/projects/connect-action-launcher-widget
  poetry build
```

Build Connect plugin:


```bash
  cd integrations
  python tools/build.py build_connect_plugin projects/connect-action-launcher-widget
```

If the build fails and action launcher widget is using beta or experimental dependencies published to Test PyPi, use the `--testpypi` flag 
to build the plugin.


### Build documentation


Install documentation dependencies:

```bash
  poetry install --only documentation
```

Build documentation:

```bash
    poetry run sphinx-build -b html doc dist/doc
```


