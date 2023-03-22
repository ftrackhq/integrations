# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack
import os

import ftrack_connect_pipeline_maya
from ftrack_connect_pipeline_qt.client import documentation


class MaxQtDocumentationClientWidget(
    documentation.QtDocumentationClientWidget
):
    '''Max documentation client'''

    documentation_path = (
        documentation.QtDocumentationClientWidget._get_user_documentation_path(
            os.path.dirname(ftrack_connect_pipeline_maya.__file__), '3DSMax'
        )
    )
