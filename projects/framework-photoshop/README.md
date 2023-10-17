ftrack Photoshop integration
############################

Community owned Photoshop integration for ftrack.

# Documentation

# Building

## Preparations

 1. Install Poetry
 2. Create a Python 3.7 virtual environment ( [Check instructions in case you are in Apple Silicon chip]((###How to install compatible PySide2 Python 3.7 on Silicon based Mac ))
 3. Activate venv
 4. Initialize Poetry and install dev dependencies:

    `$ poetry install --with development`

### How to install compatible PySide2 Python 3.7 on Silicon based Mac 

1. Open a roseta terminal:
   1. Duplicate the terminal application and check the "Open using Rosetta" checkbox inside the "Get Info" right click menu.
2. Install brew for x86_64 arch
   1.  `$ arch -x86_64 /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install.sh)" `
   2. You can create an alias named ibrew to identify the intel brew. 
      1. `$ alias ibrew="arch -x86_64 /usr/local/bin/brew"`
3. Install the python version with the intel brew
   1. `$ ibrew install python@3.7` 
4. Install virtualenv
   1. `$ /usr/local/opt/python@3.7/bin/pip3 install virtualenv`
5. Create a new virtual environment
   1. `$ /usr/local/opt/python@3.7/bin/python3 -m virtualenv /Users/ftrack/ftrack_integrations_env`
6. Activate environment:
   1. `$ source /Users/ftrack/ftrack_integrations_env/bin/activate`

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

