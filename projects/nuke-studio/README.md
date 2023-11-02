# ftrack connect NUKE STUDIO

ftrack integration with NUKE STUDIO.

Documentation: [https://ftrackhq.github.io/integrations/projects/nuke-studio/](https://ftrackhq.github.io/integrations/project/nuke-studio/)

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

Bump the connect plugin version in integrations/projects/nuke-studio/connect-plugin/__version__.py

Tag and push to SCM

### CI build

See Monorepo build CI


### Manual build

Install nuke dependencies:

```bash
  cd integrations/projects/nuke-studio
  poetry install
```

Go to the root of the package within monorepo and build the QT resources

```bash
  cd integrations
  python tools/build.py --style_path resource --output_path source/ftrack_nuke_studio/resource.py build_qt_resources projects/nuke-studio
```

Build with Poetry:

```bash
  cd integrations/projects/nuke-studio
  poetry build
```

Build Connect plugin:


```bash
  cd integrations
  python tools/build.py --include_resources resource/plugin,resource/application_hook build_connect_plugin projects/nuke-studio
```

If the build fails and Nuke Studio is using beta or experimental dependencies published to Test PyPi, use the `--testpypi` flag 
to build the plugin.


### Build documentation


Install documentation dependencies:

```bash
  poetry install --with documentation
```

Build documentation:

```bash
    poetry run sphinx-build -b html doc dist/doc
```


