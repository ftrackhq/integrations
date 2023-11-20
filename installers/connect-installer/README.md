# ftrack connect installer

Meta package that provides support for building platform specific
bundles of ftrack connect installers.

## Building

### Preparations


1. Clone the public integrations repository:

```bash
    $ git clone git@bitbucket.org:ftrack/ftrack-connect-installer.git
```

2. Install Poetry (https://python-poetry.org/docs/#installation)

3. Follow the instructions in Connect to build, then install it into the virtual environment:

```bash
    $ cd app/connect
    $ poetry install
```

Connect is now installed into the virtual environment and can be used to build the installer. Go
to the root of the Connect package within monorepo:

```bash
    $ cd integrations/installers/connect-installer
```


## Windows


Warning

( Windows only )

Visual studio and [c++ build
tools](https://visualstudio.microsoft.com/downloads/#build-tools-for-visual-studio-2019)
should be installed before install the requirements.

Reference:
([link](https://stackoverflow.com/questions/40018405/cannot-open-include-file-io-h-no-such-file-or-directory))

Note

cx_freeze branch installation is temporary until cx_freeze \> 6.5
version is released. (
[3.7](https://github.com/marcelotduarte/cx_Freeze/pull/887) )


Build msi release with:

    $ python setup.py bdist_msi

Note

Codesign process works only on machine where the key certificate is
loaded and available. Codesign also require to have the signtool.exe
installed and available.

### To codesign

#### Preparation

- Install signtool.exe from
  <https://docs.microsoft.com/en-us/dotnet/framework/tools/signtool-exe>
- If you download the Windows 10 SDK, the signtools is located here (version number may vary):
  "C:\Program Files (x86)\Windows Kits\10\bin\10.0.22621.0\x64\signtool.exe"
- Download and install the certificate .p12 certificate.

Once the msi is built, run the following commands to codesign it:

    $ signtool sign /tr http://timestamp.sectigo.com /td sha256 /fd sha256 /a <path to msi file>

At the end of the process you'll then asked to provide your token
password, once done, the package should get codesigned.


## Linux

Install patchelf platform dependent package:

    $ pip install patchelf

Build tar.gz release with:

    $ python setup.py build_exe

Once build the result will be available in
build/exe.linux-x86_64-**\<PYTHON VERSION\>**

To generate the tar.gz run from the build folder:

    $ tar -zcvf ftrack-connect-installer-<PACKAGE VERSION>-<PLATFORM>.tar.gz exe.linux-x86_64-3.7 --transform 's/exe.linux-x86_64-3.7/ftrack-connect-installer/'

Generate the md5 with:

    $ md5sum ftrack-connect-installer-<PACKAGE VERSION>-<PLATFORM>.tar.gz > ftrack-connect-installer-<PACKAGE VERSION>-<PLATFORM>.tar.gz.md5

Note

Please remember to set **\<PLATFORM\>** to either:

-   C7 for Centos 7 compatible releases.
-   C8 for centos 8 compatible releases.

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

Set your certificate id to **CODESIGN_IDENTITY**:

    $ export CODESIGN_IDENTITY="<your_certificate_id_here>"

Set your Apple username to **APPLE_USER_NAME**:

    $ export APPLE_USER_NAME="<your_apple_user>"

Set your APP-specific password generated on
<https://appleid.apple.com/account/manage> to the keychain under the
name ftrack_connect_sign_pass.

Execute the following build command and follow the instructions:

    $ python setup.py bdist_mac --codesign_frameworks --codesign --create_dmg --notarize

#### Docker

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
-   [ftrack-connect](https://bitbucket.org/ftrack/ftrack-connect) \>=
    2.0, \< 3.0
