..
    :copyright: Copyright (c) 2016 ftrack

.. _developing/hooks/verify_startup:

*****************************
ftrack.connect.verify-startup
*****************************

The *ftrack.connect.verify-startup* hook is triggered when
:term:`ftrack connect` is started and any plugins have been loaded.

The hook can be used to inform the users about problems that could arise with
the way ftrack connect is currently configured.

Example event passed to hook::

    Event(
        topic='ftrack.connect.verify-startup'
    )

Expects return data in the form::

    'Message about something that may not work as expected'

The response should either be None or a string where a string will be assumed to
be a message that should be shown to the user as a warning.

.. note::

    This event is only published through the event hub of the
    :ref:`new ftrack python API <ftrack-python-api:introduction>`.
