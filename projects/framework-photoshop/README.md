# Framework Photoshop integration

Community owned Photoshop integration for ftrack.

## Building

### Preparations


1. Install Poetry

2. Create a Python 3.7 virtual environment. If you're using an Apple Silicon chip, follow the instructions in the [How to install compatible PySide2 on Silicon based Mac](../../README.md#how-to-install-compatible-pyside2-on-silicon-based-mac) section. 

3. Activate the virtual environment. 

4. If any dependent libraries updated, make sure to release them to PyPi prior to building the plugin.

5. Update release notes.

6. Set or bump version in pyproject.toml:

```bash
    $ poetry version prerelease
```
or:
```bash
    $ poetry version patch
```
or:
```bash
    $ poetry version minor
```
or:
```bash
    $ poetry version major
```

7. If dependencies updated, update the Poetry lock file. Remember to properly validate/test the change of dependencies.

```bash
    $ poetry update
```

8. Tag and push to SCM


### CI build

See Monorepo build CI


### Manual build

1. Build with Poetry

```bash
    $ poetry build
```

2. Build Connect plugin from wheel and the locked dependencies using Monorepo custom toolset:

```bash
    cd integrations
    python tools/build.py build_connect_plugin projects/framework-photoshop
```

If the build fails and Photoshop is using beta or experimental dependencies published to Test PyPi, use the `--testpypi` flag 
to build the plugin.

To build from source, not involving PyPi, use the `--from_source` flag.


# Development


## CEP plugin

To enable live development, first allow unsigned extensions:

```bash
    defaults write com.adobe.CSXS.8 PlayerDebugMode 1
```

Build and install CEP extension and then open up permissions on folder:

```bash
    sudo chmod -R 777 "/library/application support/adobe/cep/extensions/com.ftrack.framework.photoshop.panel"
```

You are now ready to do live changes to extension, remember to sync back changes to
source folder before committing.


### CEP plugin build

Install Adobe ZXPSignCmd:

- Download and install ZXPSignCmd from: https://github.com/Adobe-CEP/CEP-Resources/tree/master/ZXPSignCMD
- If you are in MacOs, you can follow the instructions below:
  - Copy ZXPSignCmd-64bit to your Documents folder
  ```bash
    cd ~/Documents
    chmod +x ZXPSignCmd-64bit
    ln ZXPSignCmd-64bit /usr/local/bin/ZXPSignCmd
  ```

Set variables:

```bash
  export ADOBE_CERTIFICATE_PASSWORD=<Adobe exchange vault entry>
```

Build Ftrack Qt Style:

```bash
    cd integrations
    pip install -r tools/requirements.txt
    python tools/build.py build_qt_resources --css_only libs/qt-style
```

Create Adobe extension:

```bash
    cd integrations 
    python tools/build.py build_cep projects/framework-photoshop
```

## Installing

### Connect plugin
Copy the resulting dist/ftrack-framework-photoshop-<version> folder to your connect plugin folder.

### CEP plugin

Use "Extension Manager" tool provided here: https://install.anastasiy.com/ to install 
the built xzp plugin. Remember to remove previous ftrack extensions.

