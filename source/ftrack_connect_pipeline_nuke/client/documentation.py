# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack
import os

import ftrack_connect_pipeline_nuke
from ftrack_connect_pipeline_qt.client import documentation


class NukeQtDocumentationClientWidget(
    documentation.QtDocumentationClientWidget
):
    '''Nuke documentation client'''

    documentation_url = (
        "https://help.ftrack.com/en/articles/443247-ftrack-nuke-integration"
    )
