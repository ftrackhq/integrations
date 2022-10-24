..
    :copyright: Copyright (c) 2022 ftrack

.. _tutorial/load:

*******************************
Load camera image plane in Maya
*******************************

.. highlight:: bash

Next, we implement a custom camera loader within Maya that loads a reviewable Quicktime
(.mov) as an image plane, to aid animation and lighting.

Constrain camera loader
***********************

As a preparation, we constrain the camera loader to only bee seen when on animation
and lighting tasks, hiding it during modeling. We do this by modifying the loader
definition json:

**definitions/loader/maya/camera-maya-loader.json**

.. code-block:: json

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

Loading a plate onto an existing camera image plane is great to have when framing
the animation.

Definition
----------

Reviewable Quicktimes are most likely published with render (asset type), from Nuke
Studio or similar tool. This is why we implement an new *render loader* definition:

**definitions/loader/maya/render-maya-loader.json**


.. code-block:: json

    {
      "type": "loader",
      "name": "Render Loader",
      "asset_type": "render",
      "host_type": "maya",
      "ui_type": "qt",
      "contexts": [
        {
          "name": "main",
          "stages": [
            {
              "name": "context",
              "plugins":[
                {
                  "name": "context selector",
                  "plugin": "common_passthrough_loader_context",
                  "widget": "common_default_loader_context"
                }
              ]
            }
          ]
        }
      ],
      "components": [
        {
          "name": "movie",
          "file_formats": [".mov", ".r3d", ".mxf", ".avi"],
          "stages": [
            {
              "name": "collector",
              "plugins":[
                {
                  "name": "Collect components from context",
                  "plugin": "common_context_loader_collector"
                }
              ]
            },
            {
              "name": "importer",
              "plugins":[
                {
                  "name": "Import reviewable to Maya",
                  "plugin": "maya_render_loader_importer",
                  "options": {
                    "camera_name": "persp"
                  }
                }
              ]
            },
            {
              "name": "post_importer",
              "plugins":[
                {
                  "name": "maya",
                  "plugin": "common_passthrough_loader_post_importer"
                }
              ]
            }
          ]
        }
      ],
      "finalizers": [
        {
          "name": "main",
          "stages": [
            {
              "name": "pre_finalizer",
              "visible": false,
              "plugins":[
                {
                  "name": "Pre finalizer",
                  "plugin": "common_passthrough_loader_pre_finalizer"
                }
              ]
            },
            {
              "name": "finalizer",
              "visible": false,
              "plugins":[
                {
                  "name": "Finalizer",
                  "plugin": "common_passthrough_loader_finalizer"
                }
              ]
            },
            {
              "name": "post_finalizer",
              "visible": false,
              "plugins":[
                {
                  "name": "Post finalizer",
                  "plugin": "common_passthrough_loader_post_finalizer"
                }
              ]
            }
          ]
        }
      ]
    }

Definition breakdown:

 * *name*; We follow the Framework naming convention here.
 * *asset_type*: Change here if quicktimes are published onto a different custom asset type than *render*.
 * *importer plugin*; Here we reference the new **maya_render_loader_importer** that we are about to write.
 * *importer plugin options*; In the options we expose a **camera_name** attribute, which will be an option that user can change.

Render importer plugin
----------------------

Finally we implement a new importer plugin:

**plugins/maya/loader/importers/maya_render_loader_importer.py**

..  code-block:: python

    import maya.cmds as cmds

    from ftrack_connect_pipeline_maya import plugin
    import ftrack_api


    class MayaRenderLoaderImporterPlugin(plugin.MayaLoaderImporterPlugin):
        '''Maya Quicktime importer plugin'''

        plugin_name = 'maya_render_loader_importer'


        def run(self, context_data=None, data=None, options=None):
            '''Load alembic files pointed out by collected paths supplied in *data*'''

            results = {}

            camera_name = options.get('camera_name', 'persp')
            paths_to_import = []
            for collector in data:
                paths_to_import.extend(collector['result'])

            for component_path in paths_to_import:
                self.logger.debug('Importing path "{}" as image plane to camera "{}"'.format(
                    component_path, camera_name))
                imagePlane = cmds.imagePlane( camera=camera_name, fileName=component_path)
                cmds.setAttr('{}.type'.format(imagePlane[0]), 2)
                cmds.setAttr('{}.useFrameExtension'.format(imagePlane[0]), True)

                self.logger.info('Imported "{}" to {}.'.format(component_path, imagePlane[0]))

                results[component_path] = imagePlane[0]

            return results


    def register(api_object, **kw):
        if not isinstance(api_object, ftrack_api.Session):
            # Exit to avoid registering this plugin again.
            return
        plugin = MayaRenderLoaderImporterPlugin(api_object)
        plugin.register()


Plugin breakdown:

 * *plugin_name*; The name of the plugin, have to match the name used within the definition.
 * *run* function; The function that will be run during load in the ftrack Assembler.


Custom publisher plugin
-----------------------

Writing a custom publisher is very similar to writing a loader, the big difference is
that you also will have to write a *publisher collector* that collects which objects within
the DCC to publish, and also decide on component name and file format extension.

In this tutorial, we will not provide any example publisher code. Instead we refer to
the extensive set of built-in publisher for inspiration.