# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack

from Qt import QtWidgets, QtCore

from ftrack_connect_pipeline_qt.client import open
import ftrack_connect_pipeline.constants as constants
import ftrack_connect_pipeline_maya.constants as maya_constants
from ftrack_connect_pipeline_maya.utils.custom_commands import get_maya_window
from ftrack_connect_pipeline_qt import constants as qt_constants


class MayaOpenClient(open.QtOpenerClient):
    '''Open dialog and client'''

    ui_types = [
        constants.UI_TYPE,
        qt_constants.UI_TYPE,
        maya_constants.UI_TYPE,
    ]
    definition_extensions_filter = ['.mb', '.ma']

    def __init__(self, event_manager, unused_asset_list_model, parent=None):
        super(MayaOpenClient, self).__init__(
            event_manager, parent=(parent or get_maya_window())
        )

        # Make sure we stays on top of Maya
        self.setWindowFlags(QtCore.Qt.Tool)
