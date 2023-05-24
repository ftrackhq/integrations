# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack

from Qt import QtWidgets, QtCore

from ftrack_framework_qt.client import open
import ftrack_framework_core.constants as constants
import ftrack_framework_houdini.constants as houdini_constants
from ftrack_framework_qt import constants as qt_constants


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
