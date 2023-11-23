# ftrack Photoshop integration

Community owned Photoshop integration for ftrack.

# Documentation

## Building

### Preparations


Install Poetry

Create a Python 3.7 virtual environment. If you're using an Apple Silicon chip, follow the instructions in the [How to install compatible PySide2 on Silicon based Mac](../../README.md#how-to-install-compatible-pyside2-on-silicon-based-mac) section. 

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

Bump the connect plugin version in integrations/projects/framework-photoshop/connect-plugin/__version__.py

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
    python tools/build.py build_connect_plugin projects/framework-photoshop
```

If the build fails and Photoshop is using beta or experimental dependencies published to Test PyPi, use the `--testpypi` flag 
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


# Development


## CEP plugin

To enable live development, first allow unsigned extensions:

```bash
    defaults write com.adobe.CSXS.8 PlayerDebugMode 1
```

Build and install ZXP extension and then open up permissions on folder:

```bash
    sudo chmod -R 777 "/library/application support/adobe/cep/extensions/com.ftrack.framework.photoshop.panel"
```

You are now ready to do live changes to extension, remember to sync back changes to
source folder before committing.


### CEP plugin build

Set variables:

    ADOBE_CERTIFICATE_PASSWORD=<Adobe exchange vault entry>

Create Adobe extension:

```bash
    cd integrations 
    python tools/build.py build_cep projects/framework-photoshop
```

## Installing


### CEP plugin

Use "Extension Manager" tool provided here: https://install.anastasiy.com/ to install 
the built xzp plugin. Remember to remove previous ftrack extensions.

