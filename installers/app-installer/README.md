# ftrack installer

Library that provides support to build and codesign ftrack applications.

### Preparations

1. Clone the public ftrack integrations repository:

```bash
    $ git clone https://github.com/ftrackhq/integrations.git
```

2. Make sure you are in a virtual enviroment

3. Install Poetry (https://python-poetry.org/docs/#installation)

4. (Optional) Bump version, update release notes, tag and push to SCM.

5. Build and Install with dependencies

```bash
    $ cd installers/app-installer
    $ poetry update
    $ poetry install
```

### Usage

```python
    # Instantiate installer depending on the OS you want to build:
    # Use MacOSAppInstaller or LinuxAppInstaller if you are in another OS.
    from ftrack_app_installer import WindowsAppInstaller
    installer = WindowsAppInstaller(
            bundle_name="<your_app_name>",
            version="<app_version>",
            icon_path="<path_to_ico_file>", # icns for MacOS and .svg for Linux
            root_path="<path_to_your__app_repo_root>",
            entry_file_path="<path_to_app_entry_file>",
        )
    # Generate the executable and generate the installer package (optionally codesign it)
    installer.generate_executable()
    installer.generate_installer_package(codesign=true)
```

### Windows notes:

- Make sure you have Inno Setup installed: https://jrsoftware.org/isinfo.php
-  Install Java
-  Install Google cloud CLI: https://cloud.google.com/sdk/docs/install
- Make sure you have the right permissions to codesgin an ftrack app.

### MacOs notes:

- Install appdmg to be able to create the dmg: ( appdmg fails on M1 )


    $ npm install -g appdmg


- On latest version of OSX these envs are needed in order to properly
build:


    $ export CPPFLAGS=-I/usr/local/opt/openssl/include
    $ export LDFLAGS=-L/usr/local/opt/openssl/lib

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


### Linux notes:

- Install patchelf platform dependent package

    $ pip install patchelf

