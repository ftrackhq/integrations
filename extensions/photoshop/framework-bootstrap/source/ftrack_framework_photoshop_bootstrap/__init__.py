# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack
import os

from ftrack_framework_photoshop import bootstrap_integration, run_integration

# Evaluate version
try:
    from ftrack_utils.version import get_version

    __version__ = get_version(
        os.path.basename(os.path.dirname(__file__)),
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    )
except Exception:
    __version__ = '0.0.0'


# Initialise the Photoshop Framework Python standalone part.
bootstrap_integration(
    panel_launchers=[
        {
            "name": "publish",
            "label": "PUBLISHER",
            "dialog_name": "framework_publisher_dialog",
            "image": "publish",
        }
    ],
    extension_packages=[
        'ftrack_framework_common_engines',
        'ftrack_framework_common_plugins',
        'ftrack_framework_common_schemas',
        'ftrack_framework_common_tool_configs',
        'ftrack_framework_common_widgets',
    ],
)

# Run until Photoshop is closed.
run_integration()
