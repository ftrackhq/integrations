# ftrack-connect-pipeline-harmony

ftrack Connect pipeline framework Toon Boom Harmony integration

## Building

### Preparations

 #. Install Poetry
 #. Create a Python 3.7 virtual environment
 #. Activate venv
 #. Initialize Poetry and install dev dependencies:

     $ poetry install --with development

### Build package

To build the plugin from source, run:

    $ poetry build

### Build Connect plugin

    $ python <path-to-monorepo>/tools/deploy.py build_plugin

### Build docs

    $ python deploy.py build_sphinx

## Developing

    export PYTHONPATH="`pwd`/ftrack-connect-pipeline-1.3.0b2/dependencies:`pwd`/ftrack-connect-pipeline-qt-1.3.0b2/dependencies:`pwd`/ftrack-connect-pipeline-harmony-0.0.0.post5.dev0+13901f5/dependencies"
    
    export FTRACK_INTEGRATION_ID=c06cda19-001a-40d2-b2f3-13b37db270f6
    
    ftrack-connect --run-framework-standalone ftrack_connect_pipeline_harmony.bootstrap




