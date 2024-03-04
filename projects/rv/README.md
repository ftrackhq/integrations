# Rv integration

ftrack connect rv integration.

## Building

### Preparations

Update release notes.

Set or bump version in pyproject.toml:

```bash
    poetry version minor
```
or:
```bash
    poetry version major
```

Bump the connect plugin version in integrations/projects/rv/connect-plugin/__version__.py

Tag and push to SCM


### CI build

See Monorepo build CI


### Manual build

Go to the root of the RV package within monorepo:

```bash
    cd integrations/projects/rv
```
### Preparations


Build with Poetry:
    
```bash
    poetry build
```

Create the RV plugin, it will read the version number from pyproject.toml:

```bash
  cd integrations
  python tools/build.py --output_path /tmp build_rvpkg  projects/rv
```


Go to the root of the Monorepo and create the Connect plugin:

```bash
  cd integrations
  python tools/build.py --include_assets /tmp/ftrack-24.20.rvpkg  build_connect_plugin projects/rv
```


If the build fails and RV is using beta or experimental dependencies published to Test PyPi, use the `--testpypi` flag 
to build the plugin.

```bash
  cd integrations
  python tools/build.py --testpypi --include_assets /tmp/ftrack-24.0.rvpkg build_connect_plugin projects/rv
```

The Connect plugin will be output to the dist/ folder.