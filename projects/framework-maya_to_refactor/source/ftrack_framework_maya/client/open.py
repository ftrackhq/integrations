# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

from Qt import QtWidgets, QtCore

from ftrack_framework_qt.client import open
import ftrack_framework_core.constants as core_constants
from ftrack_framework_qt import constants as qt_constants
import ftrack_framework_maya.constants as maya_constants


class MayaQtOpenerClientWidget(open.QtOpenerClientWidget):
    '''Open dialog and client'''

    ui_types = [
        core_constants.UI_TYPE,
        qt_constants.UI_TYPE,
        maya_constants.UI_TYPE,
    ]
    definition_extensions_filter = ['.mb', '.ma']

    def __init__(self, event_manager, parent=None):
        super(MayaQtOpenerClientWidget, self).__init__(event_manager)

        # Make sure we stays on top of Maya
        self.setWindowFlags(QtCore.Qt.Tool)
