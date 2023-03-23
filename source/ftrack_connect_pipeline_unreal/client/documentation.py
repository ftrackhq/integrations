# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack
import os

import ftrack_connect_pipeline_unreal
from ftrack_connect_pipeline_qt.client import documentation


class UnrealQtDocumentationClientWidget(
    documentation.QtDocumentationClientWidget
):
    '''Unreal documentation client'''

    documentation_url = "https://help.ftrack.com/en/articles/3998053-ftrack-unreal-engine-integration"
