..
    :copyright: Copyright (c) 2014 ftrack

.. _developing/hooks/action_launch:

********************
ftrack.action.launch
********************

The *action.launch* hook is triggered from the ftrack interface when a user
selects an action in the :guilabel:`Actions` menu. For more information
about launching actions from the web UI, see 
:ref:`ftrack:using/actions`.

The list of actions is provided by the 
:ref:`developing/hooks/action_discover` :term:`hook`. The *action.discover*
hook provides a list of actions. All parameters from these actions are
passed to this hook and can be used when launching the action.

The default hook is a placeholder and should be extended to include correct
action commands.

Example event passed to hook::

    Event(
        topic='ftrack.action.launch',
        data=dict(
            actionIdentifier='ftrack-connect-launch-applications-action',
            applicationIdentifier='maya-2014',
            foo='bar',
            selection=[
                dict(
                    entityId='eb16970c-5fc6-11e2-bb9a-f23c91df25eb',
                    entityType='task'
                )
            ]
        )
    )

Expects reply data in the form::

    dict(
        success=True,
        message='maya-2014 launched successfully.'
    )

