..
    :copyright: Copyright (c) 2014 ftrack

*****
Setup
*****

ftrack connect nuke studio in order to work , requires to have a set of python modules and environment variables set up.

Python Modules
==============

* python-api
* ftrack-connect
* ftrack-connect-foundry

Location Plugin
===============

In Order to know where to store the material, ftrack requires to have a location setup.

.. note::
    A *studio_default* location plugin is provided as part of the resources.
    The variable $PROJECT_ROOT will have to be defined to set the root path.

Environment variables
=====================

.. code-block:: bash

    export FTRACK_SERVER=https://<server address>
    export FTRACK_APIKEY=<api key>
    export LOGNAME=<log in name>
    export PROJECT_ROOT= /mnt/projects # this should be modified accordingly to the project needs.

    export PYTHONPATH=${PYTHONPATH}:~/devel/python-api # ftrack core lib
    export PYTHONPATH=${PYTHONPATH}:~/devel/connector/ftrack-connect/source # ftrack connect lib
    export PYTHONPATH=${PYTHONPATH}:~/devel/connector/ftrack-connect-foundry/source # foundry's codebase
    export PYTHONPATH=${PYTHONPATH}:~/devel/connector/ftrack-connect-nuke-studio/source # hiero plugin

    # These are likely to be removed later on
    export FOUNDRY_ASSET_PLUGIN_PATH=~/devel/connector/ftrack-connect-nuke-studio/resource/hiero
    export HIERO_PLUGIN_PATH=~/devel/connector/ftrack-connect-nuke-studio/resource/hiero

    # Define where the processor configuration live
    export FTRACK_NUKE_STUDIO_CONFIG=~/devel/connector/ftrack-connect-nuke-studio/resource/config.json

    # Define where the processors live
    export FTRACK_PROCESSOR_PLUGIN_PATH=~/devel/connector/ftrack-connect-nuke-studio/resource/processors_plugins

    # Define the location to be used
    export FTRACK_LOCATION_PLUGIN_PATH=~/devel/connector/ftrack-connect-nuke-studio/resource/example_location


Configuration file
==================

In order to work properly, a config file has to be provide as part of the environment variables.
This file, json encoded, will contain the processors mapping against the task and the asset.

When the task is about to be created this json file will be read to see which asset (in the example named BG) will have
to be created.
The asset itself contains a mapping of which processor will be used to create and populate up the component created.


.. code-block:: json

    {
    "processor": {
            "Pull": {
                "BG": {
                    "Ingest": "processor.publish",
                    "Ingest_proxy": "processor.proxy",
                    "Thumbnail": "processor.thumbnail",
                    "Movie": "processor.review"

                }
            }
        }
    }


