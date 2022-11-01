..
    :copyright: Copyright (c) 2022 ftrack

.. _tutorial/structure:

*********************
Custom file structure
*********************

.. highlight:: bash

The tutorial relies on defining a custom folder structure across the studio.

With ftrack, and a storage scenario, comes the ``ftrack_api.structure.Standard``
structure plugin which publishes files with the standard ftrack structure:

**project/sequence/shot/model/v001/alembic.abc**

With this tutorial, we are going to provide our custom studio file structure that puts
publishes in a "PUBLISH" folder:

**project/sequence/shot/PUBLISH/anim/alembic.abc**


We are achieving this by defining our own structure plugin that we apply to the
storage scenario location. This API/Connect plugin needs to reside server side:

**mypipeline/custom-location-plugin**::

    hook/plugin_hook.py                 #  Enable structure within Connect
    location/custom_location_plugin.py  #  Initialise the location - apply structure
    location/structure.py               #  Provides the custom file structure


Structure
*********

Within the structure plugin we define an asset resolver:

**mypipeline/custom-location-plugin/location/structure.py**

.. literalinclude:: /resource/custom-location-plugin/location/structure.py
    :language: python
    :linenos:
    :emphasize-lines: 39,133-141


Location
*********

The structure are then registered and used with the default location, if it is an
unmanaged/server location, a default location at disk is used so publishes
not are lost in system temp directory:

**mypipeline/custom-location-plugin/location/custom_location_plugin.py**

.. literalinclude:: /resource/custom-location-plugin/location/custom_location_plugin.py
    :language: python
    :linenos:
    :emphasize-lines: 16-36


Source code
-----------


The complete source code for the API location structure plugin can be found here::

    resource/custom-location-plugin





