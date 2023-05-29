..
    :copyright: Copyright (c) 2016 ftrack

.. _developing/hooks/connect_widget:

************************************
ftrack.connect.plugin.connect-widget
************************************

The *ftrack.connect.plugin.connect-widget* hook is triggered when
:term:`ftrack connect` starts up and is used to register custom widgets for connect.

The hook can be used to inform the users about problems that could arise with
the way ftrack connect is currently configured.

Example event passed to hook::

    Event(
        topic='ftrack.connect.plugin.connect-widget'
    )

Expects return data in the form of a QtWidget.


.. note::

    Connect widget will be able to use the widgets provided as part of ftrack-connect.


An example is provided as part of the resources:


.. literalinclude:: /../resource/hook/example_plugin.py



