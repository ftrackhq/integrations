# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

from ftrack_connect_pipeline_qt.client.save import QtSaveClientWidget
from ftrack_connect_pipeline_harmony import utils as harmony_utils


class HarmonyQtSaveClientWidget(QtSaveClientWidget):
    '''Client for doing an incremental save of Harmony scene locally

    This is sample code that exists here for reference and not used by the current
    version of the framework.
    '''

    dcc_utils = harmony_utils
