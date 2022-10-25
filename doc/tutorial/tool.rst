..
    :copyright: Copyright (c) 2022 ftrack

.. _tutorial/tool:

*************************************************
Add a custom tool the the ftrack menu within Maya
*************************************************

In this section we demonstrate how to add your own studio tool to the Maya plug-in,
which in this case updates the status of the task you have launched to “In progress”.
We add its menu item to the ftrack menu in **userSetup.py**:

**ftrack-connect-pipeline-maya/resource/scripts/userSetup.py**

.. code-block:: python

    ..

    def initialise():

        ..

        maya_utils.init_maya()

        cmds.menuItem(                  # <---
            parent=ftrack_menu,
            label='In Progress',
            command=(functools.partial(tools.set_task_status, 'in progress', session, logger))
        )

        tools.scene_open(session, logger)


In our existing **tools.py**, we add the corresponding function:

**ftrack-connect-pipeline-maya/source/ftrack_connect_pipeline_maya/tools.py**

.. code-block:: python

    ..

    def set_task_status(status_name, session, logger, unused_arg=None):
        '''Change the status of the launched task to *status*'''
        task = session.query('Task where id={}'.format(os.environ['FTRACK_CONTEXTID'])).one()
        status = session.query('Status where name="{}"'.format(status_name)).one()
        logger.info('Changing status of task {} to {}'.format(task['name'], status_name))
        task['status'] = status
        session.commit()

