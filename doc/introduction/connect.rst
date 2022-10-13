..
    :copyright: Copyright (c) 2022 ftrack

.. _introduction/connect:

*******
Connect
*******

:term:`Connect` is the ftrack desktop GUI application enabling DCC application launch
and publishing. Connect locates the framework plugins, and together with the
:term:`Application launcher` plugin, enables discover and launch of DCC applications.

The framework modules are connect plugins, which means that need to implement a launch
hook containing the logic to discover and launch the DCC application.


Application launcher
====================

The :term:`Application launcher` is a Connect plugin responsible for discovery and
launch of DCC applications.

The application launcher reads its :term:`JSON` configuration files and performs
discovery of :term:`DCC` applications.

Example of a application launcher config:

.. code-block:: json

    {
        "priority":100,
        "context": ["Task"],
        "identifier": "ftrack-connect-launch-houdini",
        "applicationIdentifier":"houdini_{variant}",
        "integrations": {
            "pipeline":[
                "ftrack-connect-pipeline",
                "ftrack-connect-pipeline-qt",
                "ftrack-connect-pipeline-definition",
                "ftrack-connect-pipeline-houdini"
            ]
        },
        "label": "Houdini",
        "icon": "houdini",
        "variant": "core {version}",
        "search_path":{
            "linux": {
                "prefix":["/", "opt"],
                "version_expression": "(?P<version>[\\d.+]{4})",
                "expression":["hfs*", "bin", "houdinicore-bin$"]
            },
            "windows": {
                "prefix":["C:\\", "Program Files.*"],
                "expression":["Side Effects Software", "Houdini*", "bin", "houdini.exe"]
            },
            "darwin": {
                "prefix":["/", "Applications"],
                "expression": ["Houdini",  "Houdini*", "Houdini Core.*\\.app"]
            }
        },
        "console": true
    }

The tutorial part of this documentation shows an example on how to modify the
configuration.


Connect Package
===============

The :term:`Connect package` is a build of Connect, shipped as an installer, available
for each major operating system platform.



