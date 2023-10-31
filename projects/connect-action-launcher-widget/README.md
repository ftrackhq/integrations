# ftrack connect action launcher widget

Documentation: [https://ftrackhq.github.io/integrations/projects/connect-action-launcher-widget/](https://ftrackhq.github.io/integrations/projects/connect-action-launcher-widget/)


## Building


### CI build

See Monorepo build CI

### Manual build

Go to the root of the RV package within monorepo:

```bash
    cd integrations/projects/rv
```

Build with Poetry:
    
```bash
    poetry build
```


Go to the root of the Monorepo and create the Connect plugin:

```bash
  cd integrations
  python tools/build.py build_connect_plugin projects/connect-action-launcher-widget
```

If the build fails and RV is using beta or experimental dependencies published to Test PyPi, use the `--testpypi` flag 
to build the plugin.

```bash
  cd integrations
  python tools/build.py --testpypi build_connect_plugin projects/connect-action-launcher-widget
```

The Connect plugin will be output to the dist/ folder.