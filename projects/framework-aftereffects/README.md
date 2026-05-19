# ftrack After Effects integration

Community owned After Effects integration for ftrack.


## Building

### Preparations


1. Install [uv](https://docs.astral.sh/uv/)

2. If any dependent libraries updated, make sure to release them to PyPi prior to building the plugin.

3. Update release notes.

4. Set or bump version in pyproject.toml.

5. If dependencies updated, update the lock file. Remember to properly validate/test the change of dependencies.

```bash
    cd projects/framework-aftereffects
    uv lock
```

6. Tag and push to SCM


### CI build

See Monorepo build CI


### Manual build

Build with uv:

```bash
    cd projects/framework-aftereffects
    uv build
```

Build Connect plugin:


```bash
    cd integrations
    uv run python tools/build.py build_connect_plugin projects/framework-aftereffects
```

If the build fails and After Effects is using beta or experimental dependencies published to Test PyPi, use the `--testpypi` flag
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
    sudo chmod -R 777 "/library/application support/adobe/cep/extensions/com.ftrack.framework.aftereffects.panel"
```

On Windows, this folder is located here: `C:\Program Files (x86)\Common Files\Adobe\CEP\extensions`

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
    uv run python tools/build.py build_qt_resources --css_only libs/qt-style
```

Create Adobe extension:

```bash
    cd integrations
    uv run python tools/build.py build_cep projects/framework-aftereffects
```

To build without signing (for local development):

```bash
    uv run python tools/build.py --nosign build_cep projects/framework-aftereffects
```


## Installing

### Connect plugin
Copy the resulting dist/ftrack-framework-aftereffects-<version> folder to your connect plugin folder.
