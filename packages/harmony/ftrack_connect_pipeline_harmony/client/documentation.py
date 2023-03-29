# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

from ftrack_connect_pipeline_qt.client.documentation import QtDocumentationClientWidget
from ftrack_connect_pipeline_harmony import utils as harmony_utils


class HarmonyQtDocumentationClientWidget(QtDocumentationClientWidget):
    '''Harmony documentation client'''

    dcc_utils = harmony_utils
