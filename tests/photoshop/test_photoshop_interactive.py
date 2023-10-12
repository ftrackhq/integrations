
import sys
import os

# Add repository paths before running this interactive test.
INTEGRATIONS_MONO_REPO = ""
ADDITIONAL_EXTENSIONS = ""

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


# If you have additional extensions in another place you can add them here.
# for item in []: 
#     sys.path.append(
#         os.path.join(
#             ADDITIONAL_EXTENSIONS, item
#         )
#     )

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

