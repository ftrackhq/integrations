..
    :copyright: Copyright (c) 2022 ftrack

.. _standalone:

**********
Standalone
**********

.. highlight:: bash

This section describes how to use the pipeline Framework in standalone mode, from with
the DCC application or outside.

***************
Python Example
***************

This is an example on how to run the framework in a python console without
Connect or any DCC running on the background, this way the framework is able to
discover any definition where the host type is python.

**mypipeline/standalone-snippets/python_standalone_publish_snippet.py**

.. literalinclude:: /resource/standalone-snippets/python_standalone_publish_snippet.py
    :language: python
    :linenos:


*****************
DCC Maya Example
*****************

This is an example on how to run the framework inside the maya console.
All the definitions with host_type maya and python will be discovered.


.. warning::

    DCC launch is subject to be improved in future releases of the framework,
    making it possible to share launcher with Connect to enable consistent and
    context aware framework setup. For now we highly recommend to launch DCC from
    connect to avoid having to manually setup all the environment variables.

**mypipeline/standalone-snippets/maya_standalone_publish_snippet.py**

.. literalinclude:: /resource/standalone-snippets/maya_standalone_publish_snippet.py
    :language: python
    :linenos:
