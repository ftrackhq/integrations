..
    :copyright: Copyright (c) 2022 ftrack

.. _standalone:

**********
Standalone
**********

.. highlight:: bash

This section describes how to use the pipeline Framework in standalone mode, from within
the DCC application or outside.


Python Example
--------------

This is an example on how to run the framework in a python console without
Connect or any DCC running on the background, this way the framework is able to
discover any definition where the host type is python.

**mypipeline/standalone-snippets/python_standalone_publish_snippet.py**

.. literalinclude:: /resource/standalone-snippets/python_standalone_publish_snippet.py
    :language: python
    :linenos:


DCC Maya Example
----------------

This is an example on how to run the framework inside the maya console.
All the definitions with host_type maya and python will be discovered.


.. warning::

    DCC launch is subject to be improved in future releases of the framework,
    making it possible to share launcher with Connect to enable consistent and
    context aware framework setup. For now we highly recommend to launch DCC from
    connect to avoid having to manually setup all the environment variables.
    Please refer to the Discover Framework from Standalone DCC section in case
    you want to manually set them up.

**mypipeline/standalone-snippets/maya_standalone_publish_snippet.py**

.. literalinclude:: /resource/standalone-snippets/maya_standalone_publish_snippet.py
    :language: python
    :linenos:


Discover Framework from Standalone DCC
--------------------------------------

These are the necessary environment variables that has to be setup for the
framework to be discovered in a DCC application without launching from connect.

.. warning::

    This is a maya example. Please replace maya and the plugin version for your
    desired DCC and plugin version.

.. list-table:: Required Environment Variables:
   :widths: 25 75
   :header-rows: 1

   * - Name
     - Values
   * - PYTHONPATH
     - | <your-local-path-to>/ftrack-connect-plugins/ftrack-connect-pipeline-maya-1.0.2/dependencies;
       | <your-local-path-to>/ftrack-connect-plugins/ftrack-connect-pipeline-maya-1.0.2/resource/scripts;
       | <your-local-path-to>/ftrack-connect-plugins/ftrack-connect-pipeline-qt-1.0.3/dependencies;
       | <your-local-path-to>/ftrack-connect-plugins/ftrack-connect-pipeline-1.0.4/dependencies;
       | <your-local-path-to>/ftrack/ftrack-connect-plugins/ftrack-connect-pipeline-definition-1.0.3/dependencies;
       | <your-local-path-to>/ftrack/ftrack-connect-plugins/ftrack-application-launcher-1.0.6/dependencies;

   * - FTRACK_EVENT_PLUGIN_PATH
     - | <your-local-path-to>/ftrack-connect-plugins/ftrack-connect-pipeline-definition-1.0.3/resource/plugins/maya/python;
       | <your-local-path-to>/ftrack-connect-plugins/ftrack-connect-pipeline-definition-1.0.3/resource/plugins/qt/python;
       | <your-local-path-to>/ftrack-connect-plugins/ftrack-connect-pipeline-definition-1.0.3/resource/plugins/common/python;
       | <your-local-path-to>/ftrack-connect-plugins/ftrack-connect-pipeline-definition-1.0.3/resource/definitions;

   * - FTRACK_DEFINITION_PLUGIN_PATH
     - <your-local-path-to>/ftrack-connect-plugins/ftrack-connect-pipeline-definition-1.0.3/resource/plugins

   * - MAYA_SCRIPT_PATH
     - <your-local-path-to>/ftrack-connect-plugins/ftrack-connect-pipeline-maya-1.0.2/resource/scripts

