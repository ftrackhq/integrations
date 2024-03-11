# ftrack connect installer

Meta package that provides support for building platform specific
bundles of ftrack connect installers.

## Building

> **_NOTE:_** Installer is locked to cx_freeze 6.9, to make sure Qt is linked properly. pyInstaller is planned to replace cx_freeze when moving over to Qt6.


### Prerequisites

1. Make sure Connect and dependencies are updated and released accordingly.

2. Make sure version in bumped:
```
    installers/connect-installer/source/ftrack_connect_installer/_version.py
```

3. Release notes are updated in:

```
    installers/connect-installer/source/ftrack_connect_installer/release_notes.md
```

### Preparations


1. Clone the public integrations repository:

```bash
    $ git clone https://github.com/ftrackhq/integrations.git
```

2. Install Poetry (https://python-poetry.org/docs/#installation)

3. (Optional) Bump version, update release notes, tag and push to SCM.

4. Follow the instructions in Connect to build, then install it into the virtual environment:

```bash
    $ cd app/connect
    $ rm -rf dist && poetry build
```

5. Install Connect into the virtual environment:

```bash
    $ pip install dist/ftrack-connect-<VERSION>.whl
```
 
Connect is now installed into the virtual environment and can be used to build the installer. Go
to the root of the Connect package within monorepo:

```bash
    $ cd integrations/installers/connect-installer
```

Install installer dependencies, including ftrack-utils library:

```bash
    $ pip install  -r requirements.txt
```

To install using libraries from PyPy test:

```bash
    $ pip install --pre --index-url https://test.pypi.org/simple --extra-index-url https://pypi.org/simple  -r requirements.txt
```


## Windows

Visual studio and [c++ build
tools](https://visualstudio.microsoft.com/downloads/#build-tools-for-visual-studio-2019)
should be installed before install the requirements.

Reference:
([link](https://stackoverflow.com/questions/40018405/cannot-open-include-file-io-h-no-such-file-or-directory))


Build msi release with:

    $ python setup.py bdist_msi

Create the raw exe redist by compressing build\exe.win-amd64-3.7 to ZIP named:

ftrack Connect-**\<VERSION>**-win64-redist.zip

### Code sign

> **_NOTE:_** The routine is fully documented here: https://sites.google.com/backlight.co/theshire/product-development/products/integrations/deployment.


Preparations:

 -  Install Java
 -  Install Google cloud CLI: https://cloud.google.com/sdk/docs/install
 -  Authenticate:

```bash
    $ gcloud auth login
```

Build with:

```bash
    $ python setup.py bdist_msi --codesign
```



## Linux

Install patchelf platform dependent package:

```bash
    $ pip install patchelf
```

Build executable with:

```bash
    $ python setup.py build_exe
```

Once build the result will be available in
build/exe.linux-x86_64-**\<PYTHON VERSION\>**


Or to Build the tar.gz release and Md5 use:

```bash
    $ python setup.py build_exe --create_deployment
```

Sample output filename: ftrack Connect-2.1.1-C8.tar.gz



## MacOs


### Preparation

Install appdmg to be able to create the dmg:

    $ npm install -g appdmg

Note

On latest version of OSX these envs are needed in order to properly
build:

    $ export CPPFLAGS=-I/usr/local/opt/openssl/include
    $ export LDFLAGS=-L/usr/local/opt/openssl/lib

### To build without codesign

Build with:

    $ python setup.py bdist_mac

### To build and codesign

Make sure you have the certificate installed in your keychain.

Set your certificate id to **CODESIGN_IDENTITY**:

    $ export MACOS_CERTIFICATE_NAME="<your_certificate_id_here>" # Developer ID Application: your company (1111111)

To notarize you will also need to setup the following variables:
**PROD_MACOS_NOTARIZATION_APPLE_ID** # should contain your apple ID
**PROD_MACOS_NOTARIZATION_TEAM_ID** # should contain your team ID
**PROD_MACOS_NOTARIZATION_PWD** # should contain the app-specific password you can generate one in here: https://appleid.apple.com/account/manage>

    $ export PROD_MACOS_NOTARIZATION_APPLE_ID="<your_apple_id>"
    $ export PROD_MACOS_NOTARIZATION_TEAM_ID="<your_team_id>"
    $ export PROD_MACOS_NOTARIZATION_PWD="<your_app-specific_password>"

Execute the following build command and follow the instructions:

    $ python setup.py bdist_mac --codesign_frameworks --codesign --create_dmg --notarize



## Docker

As part of this repository, 3 Dockerfiles are available to sendbox the
build of ftrack-connect-installer.

-   C7.Dockerfile \[centos 7\]
-   C8.Dockerfile \[centos 8\]
-   Win10.Dockerfile \[windows 10\]

For further information, please use the README file contained in the
**docker** folder.

Note

In order to build in docker windows, you need to have a windows 10 Pro
activated and configured.

#### Known Issues

-   None

#### Dependencies

-   [Python](http://python.org) \>= 3.7, \< 3.8
-   [ftrack Utils](https://github.com/ftrackhq/integrations/libs/utils) \>=
    ^2.0.0
-   [ftrack-connect](https://github.com/ftrackhq/integrations/apps/connect) \>=
    3.0, \< 4.0
