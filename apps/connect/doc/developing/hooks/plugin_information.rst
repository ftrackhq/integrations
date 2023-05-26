..
    :copyright: Copyright (c) 2014 ftrack

.. _developing/hooks/plugin_information:

***************************************
ftrack.connect.plugin.debug-information
***************************************

The *ftrack.connect.plugin.debug-information* hook is triggered when the About
window in :term:`ftrack connect` is opened.

It can be used to return information about loaded plugins in
:term:`ftrack connect`. Such as
:ref:`actions <using/actions>`.

Example event passed to hook::

    Event(
        topic='ftrack.connect.plugin.debug-information'
    )

Expects return data in the form::

    [
        dict(
            name='ftrack connect nuke',
            version='0.1.2'
        ),
        dict(
            name='PDF Export',
            version='0.1.2',
            debug_information=dict(
                api_key='de305d54-75b4-431b-adb2-eb6b9e546014'
            )
        ),
        dict(
            name='ftrack connect package',
            version='0.2.4',
            core=True
        )
    ]

The response should be a single dictionary or a list of dictionaries and the
example response above would be displayed in the About window like this:

.. image:: /image/about_window.png

Each dictionary should contain the keys:

name
    Name of the plugin which will be displayed in the About window.

version
    Version of the plugin which will be displayed in the About window.

core
    Optional key will place the plugin under the core features instead of in
    plugins list.

debug_information
    Optional dictionary containing key/value attributes which will be
    displayed in the debug information section.
