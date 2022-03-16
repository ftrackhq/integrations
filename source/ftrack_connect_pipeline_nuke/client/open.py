# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack

from Qt import QtWidgets, QtCore

import nukescripts

from ftrack_connect_pipeline_qt.client.open import QtOpenClient
import ftrack_connect_pipeline.constants as constants
import ftrack_connect_pipeline_qt.constants as qt_constants
import ftrack_connect_pipeline_nuke.constants as nuke_constants
from ftrack_connect_pipeline_qt.ui.utility.widget.dialog import Dialog


class NukeOpenClient(QtOpenClient):
    '''Open client within dialog'''

    ui_types = [
        constants.UI_TYPE,
        qt_constants.UI_TYPE,
        nuke_constants.UI_TYPE,
    ]
    definition_extensions_filter = ['.nk']

    def __init__(self, event_manager, parent_window):
        super(NukeOpenClient, self).__init__(event_manager, parent_window)


class NukeOpenDialog(QtWidgets.QFrame):
    '''Nuke open dialog'''

    _shown = False

    def __init__(self, event_manager, unused_asset_list_model, parent=None):
        super(NukeOpenDialog, self).__init__(
            parent=parent or QtWidgets.QApplication.activeWindow()
        )
        self._event_manager = event_manager

        # Make sure we stays on top of Maya
        self.setWindowFlags(QtCore.Qt.Tool)
        self._client = None

        self.setWindowTitle('Open')
        self.move(400, 300)
        self.resize(450, 530)

    def rebuild(self):
        self.pre_build()
        self.build()

    def pre_build(self):
        self._client = NukeOpenClient(self._event_manager, self)
        self.setLayout(QtWidgets.QHBoxLayout())
        self.layout().setContentsMargins(0, 0, 0, 0)

    def build(self):
        self.layout().addWidget(self._client)

    def show(self):
        if self._shown:
            # Widget has been shown before, reset client
            self._client.setParent(None)
            self._client = None
        super(NukeOpenDialog, self).show()
        self._shown = True
        self.rebuild()
        if self._client.ask_open_assembler:
            # TODO: Search among work files and see if there is and crash scene from previous session
            dlg = Dialog(
                self,
                title='ftrack',
                question='Nothing to open, assemble a new script?',
                prompt=True,
            )
            if dlg.exec_():
                # Close and open assembler
                self.destroy()
                self._client.host_connection.launch_widget(
                    qt_constants.ASSEMBLER_WIDGET
                )
        elif self._client.ask_open_latest:
            dlg = Dialog(
                self,
                title='ftrack',
                question='Open latest?',
            )
            if dlg.exec_():
                # Trig open
                self.run_button.click()
