..
    :copyright: Copyright (c) 2022 ftrack

.. _tutorial/open:

**********************
Maya open latest scene
**********************

.. highlight:: bash

As our first task, we implement an automatic scene open in Maya upon launch. It will
check if there is a previous snapshot published on the task, if not it tries to
locate a template scene, based on the task, to load and start from.

Prerequisites
*************

 #. A shot created in ftrack, with proper timeline and fps set.
 #. The previous custom location plugin deployed, and configured storage scenario set up (preferable).
 #. A Maya template scene to use when no previous published snapshot file exists, present in project folder @ _TEMPLATES/maya/<task type>_template.mb


Implementation
**************

All DCC tools goes into the file ``custom_commands.py``:

**mypipeline/ftrack-connect-pipeline-maya/source/ftrack_connect_pipeline_maya/utils/custom_commands.py**


.. literalinclude:: /resource/ftrack-connect-pipeline-maya/source/ftrack_connect_pipeline_maya/utils/custom_commands.py
    :language: python
    :linenos:
    :lines: 1-12,232-292
    :emphasize-lines: 7,11

We are not going into detail what the ``scene_open`` function does, but it tries
to locate a previous published snapshot and if not found - a new one is copied from a template
and saved to the temp folder and opened.

Finally, to have this run during Maya startup, we add it to ``userSetup.py``:

**mypipeline/ftrack-connect-pipeline-maya/resources/scripts/userSetup.py**

.. code-block:: python
    :linenos:

    def initialise():
        ..

        maya_utils.init_maya()

        maya_utils.scene_open(session, logger)



