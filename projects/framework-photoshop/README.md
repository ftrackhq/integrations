ftrack Photoshop integration
############################

Community owned Photoshop integration for ftrack.

# Documentation

# Building

## Preparations

Follow these steps to prepare your environment:

1. Install Poetry.
2. Create a Python 3.7 virtual environment. If you're using an Apple Silicon chip, follow the instructions in the [How to install compatible PySide2 Python 3.7 on Silicon based Mac](#how-to-install-compatible-pyside2-python-37-on-silicon-based-mac) section.
3. Activate the virtual environment.
4. Initialize Poetry and install dev dependencies using the following command:
    ```bash
    poetry install --with development
    ```

### How to install compatible PySide2 Python 3.7 on Silicon based Mac 

Follow these steps to install a compatible version of PySide2 Python 3.7 on a Silicon-based Mac:

1. Open a Rosetta terminal:
    - Duplicate the terminal application and check the "Open using Rosetta" checkbox inside the "Get Info" right-click menu.
2. Install brew for x86_64 architecture:
    - Run the following command:
        ```bash
        arch -x86_64 /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install.sh)"
        ```
    - Create an alias named `ibrew` to identify the Intel brew:
        ```bash
        alias ibrew="arch -x86_64 /usr/local/bin/brew"
        ```
3. Install the Python version with the Intel brew:
    - Run the following command:
        ```bash
        ibrew install python@3.7
        ```
4. Install `virtualenv`:
    - Run the following command:
        ```bash
        /usr/local/opt/python@3.7/bin/pip3 install virtualenv
        ```
5. Create a new virtual environment and activate it:
    - Run the following command to create the virtualenv:
        ```bash
        /usr/local/opt/python@3.7/bin/python3 -m virtualenv <path-to-where-you-want-it>
        ```
    - Run the following command:
        ```bash
        source  <path-to-where-you-want-it>/bin/activate
        ```

## Build package

As monorepo tags are not interpreted by Poetry, set the version manually for now:

    $ export POETRY_DYNAMIC_VERSIONING_BYPASS="v0.4.0"

To build the plugin from source, run:

    $ poetry build

## Build Connect plugin

Until we have a proper CI/CD enabled build with Pants, use the temporary 
build script:

    $ python <path-to-monorepo>/tests/build.py build_plugin

## Build docs

    $ python <path-to-monorepo>/tests/build.py build_sphinx



# Development


## CEP plugin

To enable live development, first allow unsigned extensions:

    $ defaults write com.adobe.CSXS.8 PlayerDebugMode 1


Build and install ZXP extension and then open up permissions on folder:

    $ sudo chmod -R 777 "/library/application support/adobe/cep/extensions/com.ftrack.framework.photoshop.panel"

You are now ready to do live changes to extension, remember to sync back changes to
source folder before committing.


### CEP plugin build

Set variables:

    FTRACK_ADOBE_CERTIFICATE_PASSWORD=<Adobe exchange vault entry>

Create Adobe extension:

    $ python tests/build.py build_cep


### CEP plugin install

Use "Extension Manager" tool provided here: https://install.anastasiy.com/ to install 
the built xzp plugin. Remember to remove previous ftrack extensions.

