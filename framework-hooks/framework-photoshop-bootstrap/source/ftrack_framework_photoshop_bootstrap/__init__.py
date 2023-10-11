# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

from ftrack_framework_photoshop import bootstrap_integration, run_integration

# Initialise the Photoshop Framework Python standalone part.
bootstrap_integration(
    panel_launchers=[
        {
            "name": "publish",
            "label": "PUBLISHER",
            "dialog_name": "framework_publisher_dialog",
            "image": "publish",
        }
    ]
)

# Run until Photoshop is closed.
run_integration()
