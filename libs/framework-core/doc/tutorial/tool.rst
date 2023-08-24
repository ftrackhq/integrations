..
    :copyright: Copyright (c) 2022 ftrack

.. _tutorial/tool:

*************************************************
Add a custom tool the ftrack menu within Maya
*************************************************

In this section we demonstrate how to add your own studio tool to the Maya plug-in,
which in this case updates the status of the task you have launched to “In progress”.
We add its menu item to the ftrack menu in **userSetup.py**:

**mypipeline/projects/framework-maya/resource/scripts/userSetup.py**

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

**mypipeline/projects/framework-maya/source/ftrack_framework_maya/utils/bootstrap.py**

.. literalinclude:: /resource/framework-maya/source/ftrack_framework_maya/utils/bootstrap.py
    :language: python
    :linenos:
    :lines: 163-

