# rv

ftrack connect rv integration.

## Documentation

User documentation: https://ftrack-connect-rv.readthedocs.io/en/latest/index.html

Developer documentation: [https://ftrackhq.github.io/integrations/projects/rv/](https://ftrackhq.github.io/integrations/projects/rv/)

## Building


### CI build

See Monorepo build CI

### Manual build

Go to the root of the RV package within monorepo:

```bash
    cd integrations/projects/rv
```


Set or bump version in pyproject.toml:

```bash
    poetry version minor
```
or:
```bash
    poetry version major
```


Build with Poetry:
    
```bash
    poetry build
```


Create the RV plugin, it will read the version number from pyproject.toml:

```bash
  python build_rv_plugin.py /Users/henriknorin/Documents/ftrack/dev/git/integrations/projects/rv/resource/plugin /tmp/
```


Go to the root of the Monorepo and create the Connect plugin:

```bash
  cd integrations
  python tools/build.py --testpypi --include_assets /tmp/ftrack-5.0rc2.rvpkg  build_connect_plugin projects/rv
```


If the build fails and RV is using beta or experimental dependencies published to Test PyPi, use the `--testpypi` flag 
to build the plugin.

```bash
  cd integrations
  python tools/build.py --testpypi build_connect_plugin projects/rv
```

The Connect plugin will be output to the dist/ folder.