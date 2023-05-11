# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack

from Qt import QtWidgets, QtCore

from ftrack_connect_pipeline_qt.client import open
import ftrack_connect_pipeline.constants as constants
import ftrack_connect_pipeline_houdini.constants as houdini_constants
from ftrack_connect_pipeline_qt import constants as qt_constants


class HoudiniQtOpenerClientWidget(open.QtOpenerClientWidget):
    '''Open dialog and client'''

    ui_types = [
        constants.UI_TYPE,
        qt_constants.UI_TYPE,
        houdini_constants.UI_TYPE,
    ]
    definition_extensions_filter = ['.hip', '.hipnc']

    def __init__(self, event_manager, parent=None):
        super(HoudiniQtOpenerClientWidget, self).__init__(event_manager)

        # Make sure we stays on top of Houdini
        self.setWindowFlags(QtCore.Qt.Tool)
