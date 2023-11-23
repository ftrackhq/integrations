..
    :copyright: Copyright (c) 2022 ftrack

.. _introduction/framework/dcc:

*********************
DCC integration layer
*********************

The plugin for a specific :term:`DCC` application (maya, nuke and so on) and is
identified by the :term:`host type`. Depends on the core Framework plugins above
for bootstrapping and providing the three main Framework features:

 * Publish files/components.
 * Load files/components.
 * Asset management.

The integration achieves this by:

 * Bootstrapping the DCC app.
 * Launching the pipeline host.
 * Adding menu items to the “ftrack” menu within the DCC app, enabling launch of each :term:`client` widget.

The DCC module sits on top of the :term:`UI` layer in the pipeline Framework stack.

hook
====

The hook is designed to setup the DCC by either environment variables or arguments so it is able to find and load
the bootstrap script(s).

resource
========

The resource folder contains the bootstrap scripts, tool config configurations and the associated plugins.


bootstrap
---------
The bootstrap script is the entry point within the DCC that is responsible for
spawning the :term:`host` and :term:`client` widgets through the main DCC menu.


tool_configs
-----------

The tool config pipeline module is were the each :term:`tool config`, :term:`schema` and
Framework :term:`plugin` are stored.

As mentioned previously, the new Framework is designed to make it easy to write
custom code that takes care of asset load and publishing, the new Framework achieves
this by introducing “tool_configs” which basically are JSON schemas that configures
which Framework plugins (loaders and publishers) to run for a certain ftrack asset type.
This module is were you most likely do customisations in order to tailor the Framework
to the studio needs.

This directory contains the :term:`tool config` JSON configuration files for each
:term:`engine` and :term:`host type`.

We have highlighted some file of importance, leaving out built-in tool_configs that
would be left out of an potential customization:

.. code-block:: bash

    asset_manager/
       ..
    loader/
       ..
       geometry-maya-loader.json
    publisher/
        ..
        geometry-maya-publish.json


loader
^^^^^^

Loader tool_configs, used by the Assembler client during load of assets.

**loader/geometry-maya-loader.json**

The Framework tool_config for loading geometry asset versions into Maya:

.. code-block:: json

    {
        "type": "loader",
        "name": "Geometry Loader",
        "asset_type": "geo",
        "host_type": "maya",
        "ui_type": "qt",
        "contexts": [
            {
                "name": "main",
                "stages": [
                    {
                        "name": "context",
                        "plugins": [
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
                "name": "snapshot",
                "file_formats": [
                    ".mb",
                    ".ma"
                ],
                "stages": [
                    {
                        "name": "collector",
                        "plugins": [
                            {
                                "name": "Collect components from context",
                                "plugin": "common_context_loader_collector"
                            }
                        ]
                    },
                    {
                        "name": "importer",
                        "plugins": [
                            {
                                "name": "Import paths to Maya",
                                "plugin": "maya_native_loader_importer",
                                "options": {
                                    "load_mode": "import",
                                    "load_options": {
                                        "preserve_references": true,
                                        "add_namespace": true,
                                        "namespace_option": "file_name"
                                    }
                                }
                            }
                        ]
                    },
                    {
                        "name": "post_importer",
                        "plugins": [
                            {
                                "name": "maya",
                                "plugin": "common_passthrough_loader_post_importer"
                            }
                        ]
                    }
                ]
            },
            {
                "name": "model",
                "file_formats": [
                    ".mb",
                    ".ma"
                ],
                "stages": [
                    {
                        "name": "collector",
                        "plugins": [
                            {
                                "name": "Collect components from context",
                                "plugin": "common_context_loader_collector"
                            }
                        ]
                    },
                    {
                        "name": "importer",
                        "plugins": [
                            {
                                "name": "Import paths to Maya",
                                "plugin": "maya_native_loader_importer",
                                "options": {
                                    "load_mode": "reference",
                                    "load_options": {
                                        "preserve_references": true,
                                        "add_namespace": true,
                                        "namespace_option": "file_name"
                                    }
                                }
                            }
                        ]
                    },
                    {
                        "name": "post_importer",
                        "plugins": [
                            {
                                "name": "maya",
                                "plugin": "common_passthrough_loader_post_importer"
                            }
                        ]
                    }
                ]
            },
            {
                "name": "cache",
                "file_formats": [
                    ".abc"
                ],
                "optional": true,
                "selected": false,
                "stages": [
                    {
                        "name": "collector",
                        "plugins": [
                            {
                                "name": "Collect components from context",
                                "plugin": "common_context_loader_collector"
                            }
                        ]
                    },
                    {
                        "name": "importer",
                        "plugins": [
                            {
                                "name": "Import paths to Maya",
                                "plugin": "maya_abc_loader_importer"
                            }
                        ]
                    },
                    {
                        "name": "post_importer",
                        "plugins": [
                            {
                                "name": "maya",
                                "plugin": "common_passthrough_loader_post_importer"
                            }
                        ]
                    }
                ]
            },
            {
                "name": "game",
                "file_formats": [
                    ".fbx"
                ],
                "optional": true,
                "selected": false,
                "stages": [
                    {
                        "name": "collector",
                        "plugins": [
                            {
                                "name": "Collect components from context",
                                "plugin": "common_context_loader_collector"
                            }
                        ]
                    },
                    {
                        "name": "importer",
                        "plugins": [
                            {
                                "name": "Import paths to Maya",
                                "plugin": "maya_native_loader_importer",
                                "options": {
                                    "load_mode": "import",
                                    "load_options": {
                                        "preserve_references": true,
                                        "add_namespace": true,
                                        "namespace_option": "file_name"
                                    }
                                }
                            }
                        ]
                    },
                    {
                        "name": "post_importer",
                        "plugins": [
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
                        "plugins": [
                            {
                                "name": "Pre finalizer",
                                "plugin": "common_passthrough_loader_pre_finalizer"
                            }
                        ]
                    },
                    {
                        "name": "finalizer",
                        "visible": false,
                        "plugins": [
                            {
                                "name": "Finalizer",
                                "plugin": "common_passthrough_loader_finalizer"
                            }
                        ]
                    },
                    {
                        "name": "post_finalizer",
                        "visible": false,
                        "plugins": [
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


Attributes:

 * **type**; Tool config type, binds to the host engine names.
 * **name**; The name of the tool_config should be kept unique within the pipeline.
 * **host_type**; The type of host this tool_config should  be available to, basically the name of the DCC application.
 * **context**; Section that defines the plugin to use when selecting context (Task) and the asset version to load.
 * **components**; Section that defines each loadable component (step) - which tool_config plugin and options to use for collect and load into the DCC app. See plugin and their widgets directories below.
 * **finalizers**; Section that defines plugins that should be run after load has finished.



Publisher
^^^^^^^^^

Publisher tool_configs, used by the Publisher client during publish of assets.

The structure of a publish tool_config is very similar to the loader, with different
plugins and options.


Asset Manager
^^^^^^^^^^^^^

Plugins and options are defined that are used with the Framework asset manager client
and engine.

The Assembler dependency resolver options are defined here, and allows tuning of
which asset types are to be resolved for a certain task type.



Schema
^^^^^^^

JSON configuration files defining the rules that apply to the syntax of tool_configs
(asset manager, loader and publisher). Typically you will not alter these files,
but you can add your own attributes to tool_configs here, that can be picked up by the plugins.


plugin
------

The plugins are were the code lives, that are referenced within the tool_configs. Structure:

.. code-block:: bash

    ..
    python/
        loader/
            importers/
                widget/
                    smaya_native_loader_importer_options.py
                maya_native_loader_importer.py
                ..
            finalizers/
                maya_merge_abc_loader_finalizer.py
        publisher/
            collectors/
                widget/
                    maya_geometry_publisher_collector_options.py
                maya_geometry_publisher_collector.py
                    ..
            validators/
                maya_geometry_publisher_validator.py
                ..
            exporters/
                maya_abc_publisher_exporter.py
                ..
            finalizers/
                publish_result_maya.py
        opener/
            ..
    common/
        python/
            asset_manager/
            ..
    ..

.. code-block:: bash

    python/loader/importers/

Directory that should harbour Python plugins responsible for collecting options and do the actual loading into the DCC app.

.. code-block:: bash

    python/loader/importers/widget/maya_native_loader_importer_options.py


This Qt widget plugin defines the UI elements presented to the user, so the user
can set the load options. These load options are then read by the loader plugin below.
The name of the plugin has to be unique within Framework but can be shared with the loader
plugin:

.. code-block:: python

    ..
    class MayaNativeLoaderImporterPluginWidget(
        plugin.MayaLoaderImporterPluginWidget
    ):
        plugin_name = 'maya_native_loader_importer'
        idget = MayaNativeLoaderImporterOptionsWidget
    ..


.. code-block:: bash

    python/loader/importers/maya_native_loader_importer.py

This is the actual required DCC app plugin that reads the data from disk, as
collected by the Framework, and loads it into the current open project.


.. code-block:: bash

    python/loader/finalizers/maya_merge_abc_loader_finalizer.py

This optional plugin runs after load and here the post process of the imported
data can be performed as necessary.


.. code-block:: bash

    python/publisher/

Plugins for exporting data out from DCC app to disk and creating a version in
ftrack with reviewable and components.

.. code-block:: bash

    python/publisher/collectors/widget/maya_geometry_publisher_collector_options.py

The Qt plugin that defines the widget associated with the geometry collector,
and usually is based on the standard built in collector that adds selected objects
to a list of objects.

Set auto_fetch_on_init property to True and the fetch function within the collector
plugin will be called upon widget instantiation - enabling immediate population
of objects based on selection or other expressions/rules.

One can also define a different function, than the default “run” function, to be
executed when the plugin is run.


.. code-block:: bash

    python/publisher/collectors/maya_geometry_publisher_collector.py


The plugin that fetches objects from the loaded DCC app project to be published,
in this case Maya geometry. Depending on the type of integration, Pythonic objects
can be returned to the next stage or a path to object(s) is returned (Houdini, Unreal).

.. code-block:: bash

    python/publisher/validators/maya_geometry_publisher_validator.py

(Optional) Validator plugins that can be used to make sure the collected(selected)
objects are eligible for publish.


.. code-block:: bash

    python/publisher/output/maya_abc_publisher_exporter.py

The plugin that is responsible for exporting the collected(selected) objects to
disk, to a temporary path. The file will then be moved to its correct path dictated
by the API structure plugin associated with the location  (if a managed), upon finalization.


.. code-block:: bash

    python/publisher/finalizers/publish_result_maya.py

(Optional) Plugin that can be used to prepare the data for publish, after the output
stage is done.  A post process plugin can be implemented that runs after version have
been published, allowing for example a trigger that sends out extra notifications or
do uploads to additional storage.


Schema validation
-----------------

This host performs validation of the tool_configs at boot and when a tool_config
is supplied to be run with a engine.

The validation is important to make sure the syntax and plugin references are
correct within the tool_config.

Search the DCC log for validation errors, for example Maya log is located here:

 * Windows; **%LOCALAPPDATA%\\ftrack\\ftrack-connect\\log\\ftrack_connect_pipeline_maya.log**
 * Mac OSX; **~/Library/Application Support/ftrack-connect/log/ftrack_connect_pipeline_maya.log**
 * Linux; **~/.local/share/ftrack-connect/log/ftrack_connect_pipeline_maya.log**


source
======

Structure:

.. code-block:: bash

    asset/
    client/
    host/
    plugin/
    utils/

Description of main submodules:

 * **asset**; Contains asset manager logic for handling DCC objects.
 * **client**; DCC implementation of each :term;`client`.
 * **host**; DCC implementation of the :term;`host`.
 * **plugin**; Contain DCC implementation of bases for tool_config plugin widgets.
 * **utils**; Contains additional utils and tools related to the DCC application.

