# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack

from Qt import QtWidgets, QtCore

import nukescripts

from ftrack_connect_pipeline_qt.client.open import QtOpenClient
import ftrack_connect_pipeline.constants as constants
import ftrack_connect_pipeline_qt.constants as qt_constants
import ftrack_connect_pipeline_nuke.constants as nuke_constants


class NukeOpenClient(QtOpenClient):
    '''Open client within dialog'''

    ui_types = [constants.UI_TYPE, qt_constants.UI_TYPE, nuke_constants.UI_TYPE]
    definition_extensions_filter = ['.nk']

    def __init__(self, event_manager):
        super(NukeOpenClient, self).__init__(event_manager=event_manager)

    def get_background_color(self):
        return 'nuke'


class NukeOpenDialog(QtWidgets.QFrame):
    '''Nuke open dialog'''

    def __init__(self, event_manager):
        super(NukeOpenDialog, self).__init__(
            parent=QtWidgets.QApplication.activeWindow()
        )

        self.setWindowFlags(QtCore.Qt.Tool)
        self.setProperty('background', 'nuke')

        self._client = NukeOpenClient(event_manager)

        self.pre_build()
        self.build()
        self.post_build()

        self.shown = False

    def pre_build(self):
        self.setLayout(QtWidgets.QHBoxLayout())
        self.layout().setContentsMargins(0, 0, 0, 0)

    def build(self):
        self.layout().addWidget(self._client)

        self.setWindowTitle('Open')
        self.move(400, 300)
        self.resize(450, 530)

    def post_build(self):
        pass

    def show(self):
        if self.shown:
            # Widget has been shown before, reset client
            self._client.context_selector.set_default_context_id()
        super(NukeOpenDialog, self).show()
        self.shown = True
