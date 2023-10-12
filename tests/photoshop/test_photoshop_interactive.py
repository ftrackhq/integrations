
import sys
import os

# Add repository paths before running this interactive test.
INTEGRATIONS_MONO_REPO = ""
INTEGRATIONS_OPEN_SAVE_TOOL_SAMPLE_REPO = ""

for item in (
    "framework-hooks/framework-photoshop-bootstrap/source/",
    "framework-hooks/framework-core-schemas/source",
    "framework-hooks/framework-core-engines/source",
    "framework-hooks/framework-core-plugins/source",
    "framework-hooks/framework-core-widgets/source",
    "projects/framework-photoshop/source",
    "libs/constants/source",
    "libs/utils/source",
    "libs/framework-core/source/",
    "libs/framework-widget/source/",
    "libs/framework-plugin/source/",
    "libs/framework-engine/source/",
    "libs/qt/source",
    "libs/qt-style/source",
):
    sys.path.append(os.path.join(INTEGRATIONS_MONO_REPO, item))

for item in (
    "framework-hooks/framework-photoshop-tool-configs/source/",
    "framework-hooks/framework-photoshop-plugins/source/",
    "framework-hooks/framework-photoshop-widgets/source/",
): 
    sys.path.append(
        os.path.join(
            INTEGRATIONS_OPEN_SAVE_TOOL_SAMPLE_REPO, item
        )
    )

import ftrack_framework_photoshop_bootstrap

ftrack_framework_photoshop_bootstrap.bootstrap_integration(
    panel_launchers=[
        {
            "name": "publish",
            "label": "PUBLISHER",
            "dialog_name": "framework_publisher_dialog",
            "image": "publish",
        }
    ]
)

