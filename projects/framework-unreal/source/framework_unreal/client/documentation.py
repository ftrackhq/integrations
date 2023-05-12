# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack
import os

import framework_unreal
from framework_qt.client import documentation


class UnrealQtDocumentationClientWidget(
    documentation.QtDocumentationClientWidget
):
    '''Unreal documentation client'''

    documentation_url = "https://help.ftrack-studio.backlight.co/hc/en-us/articles/13130003888023"
