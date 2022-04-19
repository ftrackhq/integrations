# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack

from Qt import QtWidgets, QtCore

from ftrack_connect_pipeline_qt.client.open import QtOpenClient
import ftrack_connect_pipeline.constants as constants
import ftrack_connect_pipeline_qt.constants as qt_constants
import ftrack_connect_pipeline_nuke.constants as nuke_constants
from ftrack_connect_pipeline_qt.ui.utility.widget import dialog
from ftrack_connect_pipeline_nuke.utils.custom_commands import get_nuke_window


class NukeOpenClient(QtOpenClient):
    '''Open client within dialog'''

    ui_types = [
        constants.UI_TYPE,
        qt_constants.UI_TYPE,
        nuke_constants.UI_TYPE,
    ]
    definition_extensions_filter = ['.nk']

    def __init__(self, event_manager, parent=None):
        super(NukeOpenClient, self).__init__(event_manager, parent=parent)


class NukeOpenDialog(dialog.Dialog):
    '''Nuke open dialog'''

    _shown = False

    def __init__(self, event_manager, unused_asset_list_model, parent=None):
        super(NukeOpenDialog, self).__init__(parent or get_nuke_window())
        self._event_manager = event_manager

        # Make sure we stays on top of Maya
        self.setWindowFlags(QtCore.Qt.Tool)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose, False)

        self.pre_build()
        self.build()

        self.setWindowTitle('Open')
        self.move(400, 300)
        self.resize(450, 530)

    def pre_build(self):
        self._client = NukeOpenClient(
            self._event_manager, parent=self.parent()
        )
        self.setLayout(QtWidgets.QHBoxLayout())
        self.layout().setContentsMargins(0, 0, 0, 0)

    def build(self):
        self.layout().addWidget(self._client)

    def show(self):
        if self._shown:
            # Widget has been shown before, recreate client
            self._client.reset()
        super(NukeOpenDialog, self).show()
        self._shown = True

    def closeEvent(self, event):
        '''Nuke deletes the dialog, instead hide it so it can be reused'''
        self.setVisible(False)
        event.ignore()
