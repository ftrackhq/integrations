# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack
import os

import ftrack_connect_pipeline_3dsmax
from ftrack_connect_pipeline_qt.client import documentation


class MaxQtDocumentationClientWidget(
    documentation.QtDocumentationClientWidget
):
    '''Max documentation client'''

    documentation_url = (
        "https://help.ftrack.com/en/articles/443239-ftrack-3ds-max-integration"
    )
