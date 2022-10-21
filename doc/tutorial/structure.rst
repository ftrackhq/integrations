..
    :copyright: Copyright (c) 2022 ftrack

.. _tutorial/structure:

*********************
Custom file structure
*********************

.. highlight:: bash

The tutorial relies on defining a custom folder structure across the studio.

With ftrack, and a storage scenario, comes the ftrack_api.structure.Standard
structure plugin which publishes files with the standard ftrack structure::

    project/sequence/shot/model/v001/alembic.abc

With this tutorial, we are going to provide our custom studio file structure that puts
publishes in a "PUBLISH" folder::

    project/sequence/shot/PUBLISH/anim/alembic.abc


We are achieving this by defining our own structure plugin that we apply to the
storage scenario location. This API/Connect plugin needs to reside server side::

    PIPELINE/custom-location-plugin:

    hook
    hook/plugin_hook.py			        #  Enable structure within Connect
    location/custom_location_plugin.py	#  Initialise the location - apply structure
    location/structure.py			    #  Provides the custom file structure


Structure
*********

Within the structure plugin we define an asset resolver::

    PIPELINE/custom-location-plugin/location/structure.py

.. code-block:: python

    ..
    STUDIO_PUBLISH_FOLDER = "PUBLISH"
    ..
        def __init__(
            ..
            self.resolvers = OrderedDict({
                ..
                'Task': self._resolve_task,
    ..
        def _resolve_asset(self, asset, context=None):
            '''Build resource identifier for *asset*.'''
            # Resolve parent context
            parts = self._resolve_context_entity(asset['parent'], context=context)
            # Framework guide customisation - publish to shot/asset "publish" subfolder
            parts.append(STUDIO_PUBLISH_FOLDER)
            # Base on its name
            parts.append(self.sanitise_for_filesystem(asset['name']))
            return parts
    ..



Location
*********

The structure are then registered and used with the default location, if it is an
unmanaged location/storage scenario, a default location at disk is used so publishes
not are lost in system temp directory:

.. code-block:: python

    ..

    def configure_location(session, event):
        '''Apply our custom structure to default storage scenario location.'''
        import structure

        DEFAULT_USER_DISK_PREFIX = os.path.join(
            os.path.expanduser('~'),
            'Documents',
            'ftrack_tutorial'
        )

        location = session.pick_location()
        location.accessor = ftrack_api.accessor.disk.DiskAccessor(
            prefix=DEFAULT_USER_DISK_PREFIX
        )
        location.structure = structure.Structure()
        #location.priority = 1

        logger.info(
            u'Registered custom file structure at location "{0}", path: {1}.'.format(
                location['name'], DEFAULT_USER_DISK_PREFIX)
        )

Source code
***********


The complete source code for the API location structure plugin can be found here::

    resource/custom-location-plugin





