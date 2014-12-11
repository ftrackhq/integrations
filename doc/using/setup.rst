Setup
*****

ftrack connect nuke studio in order to work , requires to have a set of python modules and environment variables set up.

Python Modules
==============

* ftrackCoreApi
* ftrack-connect
* ftrack-connect-foundry


Environment variables
=====================

.. code-block:: bash

    export FTRACK_SERVER=https://<server address>
    export FTRACK_APIKEY=<api key>
    export LOGNAME=<log in name>

    export PYTHONPATH=${PYTHONPATH}:~/devel/python-api # ftrack core lib
    export PYTHONPATH=${PYTHONPATH}:~/devel/connector/ftrack-connect/source # ftrack connect lib
    export PYTHONPATH=${PYTHONPATH}:~/devel/connector/ftrack-connect-foundry/source # foundry's codebase
    export PYTHONPATH=${PYTHONPATH}:~/devel/connector/ftrack-connect-nuke-studio/source # hiero plugin
    export FOUNDRY_ASSET_PLUGIN_PATH=~/devel/connector/ftrack-connect-nuke-studio/resource/hiero
    export HIERO_PLUGIN_PATH=~/devel/connector/ftrack-connect-nuke-studio/resource/hiero
