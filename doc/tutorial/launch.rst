..
    :copyright: Copyright (c) 2022 ftrack

.. _tutorial/launch:

**********************
Customising DCC launch
**********************

Here we are going to demonstrate how to disable Maya launcher for the compositing(task type)
department, we do this by modifying the Maya launcher hook:


**mypipeline/ftrack-connect-pipeline-maya/hook/discover_maya.py**

..  code-block:: python
    :linenos:
    :emphasize-lines: 16-18

    ..

    def on_discover_maya_pipeline(session, event):
        from ftrack_connect_pipeline_maya import __version__ as integration_version

        data = {
            'integration': {
                "name": 'ftrack-connect-pipeline-maya',
                'version': integration_version
            }
        }

        # Disable maya launch on certain task types
        task = session.get('Context', selection[0]['entityId'])

        if task['type']['name'].lower() in ['compositing']:
            # Do not show Maya launchers compositing task launch
            data['integration']['disable'] = True

    ..


The implementation is pretty straightforward, as Connect emits a discover event,
the maya hook checks the task type and disables the launcher accordingly.

Within the same hook, you can also augment the environment variables sent to Nuke.


Changing paths to DCC executables and arguments
***********************************************

In some cases, you might want to change the location of DCC executables or the
arguments passed on. This is done by modifying the configs within configuration
of the ``ftrack-application-launcher`` module.

In this example we are going to change the Windows location of Maya and add an argument:

**ftrack-application-launcher/resource/config/maya-pipeline.json**

..  code-block:: json
    :linenos:
    :emphasize-lines: 24,26

    {
        "priority":100,
        "context": ["Task"],
        "identifier": "ftrack-connect-launch-maya",
        "applicationIdentifier":"maya_{variant}",
        "integrations": {
            "pipeline":[
                "ftrack-connect-pipeline-definition",
                "ftrack-connect-pipeline",
                "ftrack-connect-pipeline-qt",
                "ftrack-connect-pipeline-maya"
            ]
        },
        "label": "Maya",
        "icon": "maya",
        "variant": "{version}",
        "search_path":{
            "linux": {
                "prefix":["/", "usr","autodesk","maya.+"],
                "expression":["bin","maya$"],
                "version_expression": "maya(?P<version>\\d{4})"
            },
            "windows": {
                "prefix":["E:\\", "Program Files.*"],
                "expression":["Autodesk", "Maya.+", "bin", "maya.exe"],
                "launch_arguments": ["-pythonver","2"]
            },
            "darwin": {
                "prefix":["/", "Applications"],
                "expression": ["Autodesk", "maya.+", "Maya.app"]
            }
        },
        "console": true
     }


The changes we have done:

 * Changed the Windows Maya executable base path to E: instead of C:
 * Added the arguments "-pythonver 2" to Maya.


References
----------

Find full documentation on how to create a launcher here: :doc:`ftrack Application Launcher developer documentation <ftrack-application-launcher:developing>`




