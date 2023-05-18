..
    :copyright: Copyright (c) 2016 ftrack

.. _developing/tutorial/adding_a_location:

************************
Adding a location plugin
************************

This tutorial assumes basic knowledge of the
:term:`Location plugins <location plugin>` system in ftrack and will focus on
how to make Location plugins available for Connect and integrated applications.

Making Connect aware of your location plugin
============================================

Using the :term:`plugin directory` we can register a location plugin to
be available in Connect. Let us now implement a basic Location plugin

    .. code-block:: python

        import ftrack_api

        def configure_locations(event):
            session = event['data']['session']

            location = session.ensure(
                'Location', {
                    'name': 'studio.location'
                }
            )

            location.priority = 0
            location.structure = ftrack_api.structure.standard.StandardStructure()

            location.accessor = ftrack_api.accessor.disk.DiskAccessor(
                prefix=prefix='<path-to-directory-where-files-should-go>'
            )

        def register(session, **kw):

            # Validate that session is an instance of ftrack_api.Session. If not,
            # assume that register is being called from an incompatible API
            # and return without doing anything.
            if not isinstance(session, ftrack_api.Session):
                # Exit to avoid registering this plugin again.
                return

            session.event_hub.subscribe(
                'topic=ftrack.api.session.configure-location',
                configure_locations
            )



If we add our new location plugin, ``custom_location_plugin.py``, to the
plugin directory it will be automatically registered and available in Connect::

    <ftrack-connect-plugin-directory>/
        my_location_plugin/
            hook/
                location/
                    custom_location_plugin.py

.. _developing/tutorial/adding_a_location/modifying_application_launch:
