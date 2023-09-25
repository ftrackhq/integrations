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

    $ export POETRY_DYNAMIC_VERSIONING_BYPASS="v0.4.0a7"

To build the plugin from source, run:

    $ poetry build

## Build Connect plugin

Until we have a proper CI/CD enabled build with Pants, use the temporary 
build script:

    $ python <path-to-monorepo>/tests/build.py build_plugin

## Build docs

    $ python <path-to-monorepo>/tests/build.py build_sphinx