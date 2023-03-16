# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack
import os

import ftrack_connect_pipeline_unreal
from ftrack_connect_pipeline_qt.client import documentation


class UnrealQtDocumentationClientWidget(
    documentation.QtDocumentationClientWidget
):
    '''Unreal documentation client'''

    documentation_path = (
        documentation.QtDocumentationClientWidget._get_user_documentation_path(
            os.path.dirname(ftrack_connect_pipeline_unreal.__file__), 'unreal'
        )
    )
