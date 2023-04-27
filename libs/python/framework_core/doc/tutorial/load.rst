..
    :copyright: Copyright (c) 2022 ftrack

.. _tutorial/load:

*******************************
Load camera image plane in Maya
*******************************

.. highlight:: bash

Next, we implement a custom camera loader within Maya that loads a reviewable Quicktime
(.mov) as an image plane, to aid animation and lighting framing.


Constrain camera loader
***********************

As a preparation, we constrain the camera loader to only be seen when on animation
and lighting tasks, hiding it during modelling. We do this by modifying the loader
definition json and adding the **discoverable** key:

**mypipeline/ftrack-connect-pipeline-definitions/resource/definitions/loader/maya/camera-maya-loader.json**

..  code-block:: json
    :linenos:
    :emphasize-lines: 7

    {
        "type": "loader",
        "name": "Camera Loader",
        "asset_type": "cam",
        "host_type": "maya",
        "ui_type": "qt",
        "discoverable": ["animation","lighting"]

    }

Here we have added the additional *discoverable* key with associate task type names.


Render loader
*************

This serves as an example on how to implement your own loader that is not part of
the framework but required in production.


Definition
----------

Reviewable Quicktimes are most likely published with render (asset type), from Nuke
Studio or similar tool. This is why we implement an new *render loader* definition:

**mypipeline/ftrack-connect-pipeline-definitions/resource/definitions/loader/maya/render-maya-loader.json**

.. literalinclude:: /resource/ftrack-connect-pipeline-definition/resource/definitions/loader/maya/render-maya-loader.json
    :language: json
    :linenos:
    :emphasize-lines: 3,4,26-27,43-46


Definition breakdown:

 * *name*; We follow the Framework naming convention here.
 * *asset_type*: Change here if quicktimes are published onto a different custom asset type than *render*.
 * *component name*; The name of loadable components on an asset version.
 * *component file formats/types*; List of file format extensions supported by the loader plugin.
 * *importer plugin*; Here we reference the new **maya_render_loader_importer** that we are about to write.
 * *importer plugin options*; In the options we expose a **camera_name** attribute, which will be an option that the user can change.

Render importer plugin
----------------------

Finally we implement a new importer plugin:

**mypipeline/ftrack-connect-pipeline-definitions/ftrack-connect-pipeline-definition/resource/plugins/maya/python/loader/importers/maya_render_loader_importer.py**

.. literalinclude:: /resource/ftrack-connect-pipeline-definition/resource/plugins/maya/python/loader/importers/maya_render_loader_importer.py
    :language: python
    :linenos:
    :emphasize-lines: 13,15-43

Plugin breakdown:

 * *plugin_name*; The name of the plugin, have to match the name used within the definition.
 * *run* function; The function that will be run during load in the ftrack Assembler.


Custom publisher plugin
-----------------------

Writing a custom publisher is very similar to writing a loader, the big difference is
that you also will have to write a *publisher collector* that collects which objects within
the DCC to publish, and also decide on component name and file format extension.

In this tutorial, we will not provide any example publisher code. Instead we refer to
the extensive set of built-in publishers for inspiration.