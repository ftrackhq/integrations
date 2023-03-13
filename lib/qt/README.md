# ftrack-connect-pipeline-qt

Qt driven ftrack Connect pipeline framework UI layer

## Building

### Preparations

 #. Install Poetry
 #. Create a Python 3.7 virtual environment
 #. Activate venv
 #. Initialize Poetry and install dev dependencies:

     $ poetry install --with development


### Build QT resources

    $ python deploy.py build_resources

### Build package

To build the plugin from source, run:

    $ poetry build

### Build Connect plugin

    $ python deploy.py build_plugin

### Build docs

    $ python deploy.py build_sphinx



