..
    :copyright: Copyright (c) 2014 ftrack

.. _developing/hooks/action_discover:

**********************
ftrack.action.discover
**********************

The *action.discover* hook is triggered from the ftrack interface to request a
list of available actions for launching. For more information, see 
:ref:`ftrack:using/actions`.

The default hook is a placeholder and should be extended to include a complete
list of actions that can be launched.

Example event passed to hook::

    Event(
        topic='ftrack.action.discover',
        data=dict(
            selection=[
                dict(
                    entityId='eb16970c-5fc6-11e2-bb9a-f23c91df25eb',
                    entityType='task',
                )
            ]
        )
    )

Expects reply data in the form::

    dict(
        items=[
            dict(
                label='Mega Modeling',
                variant='2014',
                actionIdentifier='ftrack-connect-launch-applications-action',
                icon='URL to custom icon or predefined name',
                applicationIdentifier='mega_modeling_2014'
            ),
            dict(
                label='Professional Painter',
                icon='URL to custom icon or predefined name',
                actionIdentifier='ftrack-connect-launch-applications-action',
                applicationIdentifier='professional_painter'
            ),
            dict(
                label='Cool Compositor',
                variant='v2',
                actionIdentifier='ftrack-connect-launch-applications-action'
                icon='URL to custom icon or predefined name',
                applicationIdentifier='cc_v2',
                cc_plugins=['foo', 'bar']
            )
        ]
    )

The response should be a dictionary with an ``items`` list. The list should
contain a dictionary for each menu item to be returned.

Action
======

To add an action, add an item in the following format.

.. code-block:: python

    dict(
        label='Crazy Compositor',
        actionIdentifier='ftrack-connect-launch-applications-action',
        variant='v2',
        description='Launch Crazy Compositor',
        icon='URL to custom icon or predefined name',
        cc_plugins=['foo', 'bar'],
        applicationIdentifier='cc_v2'
    )

The different options are:

label
    Used to display the action in the ftrack interface. 

actionIdentifier
    Used to target a specific callback for an action.

variant
    A variant of the action, such as application version.

description
    A helpful description for the user.

icon
    Icon to display in the ftrack interface. Can be either an URL to a custom
    icon or the name of a predefined icon. Predefined icons are ``hiero``,
    ``hieroplayer``, ``nuke``, ``nukex``, ``maya``, ``premiere`` and 
    ``default``

    In addition, you can add any extra data you want to include in the event.
    The data returned will be passed on to the 
    :ref:`developing/hooks/action_launch` hook.

    In the default hook each item contains an ``applicationIdentifier``
    which is used to uniquely identify which application to start.

