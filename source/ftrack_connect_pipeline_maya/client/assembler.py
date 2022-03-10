# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack

from Qt import QtWidgets, QtCompat, QtCore

from ftrack_connect_pipeline_maya.constants.asset import modes as load_const

from ftrack_connect_pipeline_qt.client.assembler import QtAssemblerClient
import ftrack_connect_pipeline.constants as constants
import ftrack_connect_pipeline_qt.constants as qt_constants
import ftrack_connect_pipeline_maya.constants as maya_constants
from ftrack_connect_pipeline_maya.utils.custom_commands import get_maya_window


class MayaAssemblerClient(QtAssemblerClient):
    '''Open client within dialog'''

    ui_types = [
        constants.UI_TYPE,
        qt_constants.UI_TYPE,
        maya_constants.UI_TYPE,
    ]

    def __init__(self, event_manager, asset_list_model, parent_window):
        super(MayaAssemblerClient, self).__init__(
            event_manager,
            load_const.LOAD_MODES,
            asset_list_model,
            parent_window,
        )


class MayaAssemblerDialog(QtWidgets.QDialog):
    '''Maya assembler & importer dialog'''

    _shown = False

    def __init__(self, event_manager, asset_list_model):
        super(MayaAssemblerDialog, self).__init__(parent=get_maya_window())
        self._event_manager = event_manager
        self._asset_list_model = asset_list_model

        self._client = None

        # Make sure we stays on top of Maya
        self.setWindowFlags(QtCore.Qt.Tool)

        self.rebuild()

        # self.setModal(True)
        self.setWindowTitle('ftrack Connect Assembler')
        self.resize(1000, 500)

    def rebuild(self):
        self.pre_build()
        self.build()

    def pre_build(self):
        self._client = MayaAssemblerClient(
            self._event_manager, self._asset_list_model, self
        )
        self.setLayout(QtWidgets.QHBoxLayout())
        self.layout().setContentsMargins(0, 0, 0, 0)

    def build(self):
        self.layout().addWidget(self._client)

    def show(self):
        if self._shown:
            # Widget has been shown before, reload dependencies
            self._client.reset()

        super(MayaAssemblerDialog, self).show()
        self._shown = True
