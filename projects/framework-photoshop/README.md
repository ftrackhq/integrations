ftrack Photoshop integration
############################

Community owned Photoshop integration for ftrack.

# Documentation

# Building

## Preparations

 #. Install Poetry
 #. Create a Python 3.7 virtual environment
 #. Activate venv
 #. Initialize Poetry and install dev dependencies:

     $ poetry install --with development

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