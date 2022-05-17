# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack

from Qt import QtWidgets, QtCore

from ftrack_connect_pipeline_qt.client import open
import ftrack_connect_pipeline.constants as constants
import ftrack_connect_pipeline_qt.constants as qt_constants
import ftrack_connect_pipeline_nuke.constants as nuke_constants
from ftrack_connect_pipeline_nuke.utils.custom_commands import get_main_window


class NukeOpenerClient(open.QtOpenerClient):
    '''Nuke open dialog'''

    ui_types = [
        constants.UI_TYPE,
        qt_constants.UI_TYPE,
        nuke_constants.UI_TYPE,
    ]
    definition_extensions_filter = ['.nk']

    def __init__(self, event_manager, unused_asset_list_model, parent=None):
        super(NukeOpenerClient, self).__init__(
            event_manager, parent=(parent or get_main_window())
        )
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose, False)
        # Make toolbar smaller
        self.setWindowFlags(QtCore.Qt.Tool)

    def closeEvent(self, event):
        '''Nuke deletes the dialog, instead hide it so it can be reused'''
        self.setVisible(False)
        event.ignore()

    def show(self):
        super(NukeOpenerClient, self).conditional_rebuild()
        super(NukeOpenerClient, self).show()
