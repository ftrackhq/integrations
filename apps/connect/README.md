# ftrack Connect

Core for ftrack connect providing main service that enhances
functionality of the ftrack web server and also provides standalone
applications for workflows including logging time and publishing assets.

## Documentation

Full documentation, including installation and setup guides, can be
found at <https://developer.ftrack.com/integrating-pipelines/connect/>

## Building

### Preparations

1. Clone the public repository:

    $ git clone https://github.com/ftrackhq/integrations.git

2. Update release notes.

3. Install Poetry (https://python-poetry.org/docs/#installation)

4. Set or bump version in pyproject.toml:

```bash
   cd integrations/apps/connect
```


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

5. Tag and push to SCM


### Test connect from sources

1. Go to the Connect package within monorepo:

```bash
    cd integrations/apps/connect
```

2. Create and activate a virtual environment:
- Create a Python 3.10 virtual environment. If you're using an Apple Silicon chip, follow the instructions in the [How to install compatible PySide2 on Silicon based Mac](../../README.md#how-to-install-compatible-pyside2-on-silicon-based-mac) section.
- Activate the virtual environment. 

3. Update dependencies:

```bash
    poetry update
```

4. Install dependencies:

```bash
    poetry install --extras ftrack-libs framework-libs # If you want to manually use ftrack-libraries from sources, don't install extras and manually install them following its own readme file.
```
   1. To install framework-libs from sources:
   ```bash
       cd ../../libs/framework-core
       poetry install
   ```

   2. To install ftrack-libs from sources:
   ```bash
       cd ../../libs/utils
       poetry install
   ```

5. Start connect:

```bash
    python -m ftrack_connect
```

### Manual build

1. Go to the Connect package within monorepo:

```bash
    cd integrations/apps/connect
```

2. Create and activate a virtual environment:
- Create a Python 3.7 virtual environment. If you're using an Apple Silicon chip, follow the instructions in the [How to install compatible PySide2 on Silicon based Mac](../../README.md#how-to-install-compatible-pyside2-on-silicon-based-mac) section.
- Activate the virtual environment. 

3. Update dependencies:

```bash
    poetry update
```

4. Install dependencies:

```bash
    poetry install --extras ftrack-libs framework-libs
```

5. Build the QT resources

```bash
cd ../..
pip install -r tools/requirements-connect.txt
python tools/build.py build_qt_resources --style_path resource --output_path source/ftrack_connect/ui/resource.py --pyside_version 6 apps/connect
cd integrations/apps/connect
```

7. Build with Poetry:

```bash
  cd integrations/apps/connect
  poetry build
```

8. Install the wheel:

```bash
  pip install dist/ftrack-connect-<version>.whl
```


### Create installer

The ftrack Connect installer is a self-extracting executable that contains the
Connect desktop application and the required dependencies. Installers for Windows,
Mac and Linux are supported, and are triggered upon release within the ftrack
Integrations monorepo Githib Action workflows.

To create an installer manually, follow the instructions below:

Preparations:

- Set the version in `connect-installer/__version__.py` to the desired version.
- Update the release notes in `release_notes.md`.
- Tag an release

1. Create a Python 3.10 virtual environment.
2. Install Poetry (https://python-poetry.org/docs/#installation)
3. Go to the Connect package within monorepo and install Connect:

```bash
    cd integrations/apps/connect
    poetry install
```
4. Build the QT resources

```bash
python tools/build.py --style_path resource --output_path source/ftrack_connect/ui/resource.py build_qt_resources --pyside_version 6 apps/connect
```

5. Install the required dependencies (pyinstaller):

```bash
    pip install -r apps/connect/connect-installer/requirements.txt
```

6. Build the installer:

To on only build an executable, run:

```bash
python tools/build.py build_connect apps/connect
```

The output will be in the `dist` folder of apps/connect package.


**Build installer on Windows:**

To build the installer on Windows, add the --create_installer flag:

```bash
python tools/build.py build_connect --create_installer apps/connect 
```

To codesign on Windows, add the --codesign flag. Remember to authenticate with Google cloud before doing so:

```bash
python tools/build.py build_connect --codesign --create_installer apps/connect 
```


**Build installer on Mac:**

To build the installer in Mac, add the --create_installer flag:

```bash
python tools/build.py build_connect --create_dmg apps/connect 
```

To codesign on Mac, add the --codesign and --notarise flag:

```bash
python tools/build.py build_connect --codesign --notarise --create_dmg apps/connect 
```


**Build installer on Linux:**

To build the installer in Linux, add the --create_archive flag:

```bash
python tools/build.py build_connect --create_archive apps/connect 
```

Note: On Linux it might complain about a share library missing, recompile Python 3.10 with the `--enable-shared` flag 
and add the path to the shared library path (`/usr/local/lib`) to the `LD_LIBRARY_PATH` environment variable.

```bash

### Build documentation

1. Install documentation dependencies:

```bash
  poetry install --only documentation
```

2. Build documentation:

```bash
    poetry run sphinx-build -b html doc dist/doc
```

## Publish to PyPi

This is performed by the CI, to publish to PyPi test - follow the instructions in integrations README.md at root level of 
repository.

