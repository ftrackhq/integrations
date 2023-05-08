..
    :copyright: Copyright (c) 2022 ftrack

.. _tutorial/tool:

*************************************************
Add a custom tool the the ftrack menu within Maya
*************************************************

In this section we demonstrate how to add your own studio tool to the Maya plug-in,
which in this case updates the status of the task you have launched to “In progress”.
We add its menu item to the ftrack menu in **userSetup.py**:

**mypipeline/ftrack-connect-pipeline-maya/resource/scripts/userSetup.py**

.. code-block:: python
    :linenos:
    :emphasize-lines: 9-13

    ..

    def initialise():

        ..

        maya_utils.init_maya()

        cmds.menuItem(
            parent=ftrack_menu,
            label='In Progress',
            command=(functools.partial(maya_utils.set_task_status, 'in progress', session, logger))
        )

        maya_utils.scene_open(session, logger)


In DCC **custom_commands.py**, we add the corresponding ``set_task_status`` function:

**mypipeline/ftrack-connect-pipeline-maya/source/ftrack_connect_pipeline_maya/utils/custom_commands.py**

.. literalinclude:: /resource/ftrack-connect-pipeline-maya/source/ftrack_connect_pipeline_maya/utils/custom_commands.py
    :language: python
    :linenos:
    :lines: 295-

