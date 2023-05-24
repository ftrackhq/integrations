# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack

from Qt import QtWidgets, QtCore

from ftrack_framework_qt.client import open
import ftrack_framework_core.constants as constants
import ftrack_framework_3dsmax.constants as max_constants
from ftrack_framework_qt import constants as qt_constants
from ftrack_framework_3dsmax import utils as max_utils


class MaxQtOpenerClientWidget(open.QtOpenerClientWidget):
    '''Open dialog and client'''

    ui_types = [
        constants.UI_TYPE,
        qt_constants.UI_TYPE,
        max_constants.UI_TYPE,
    ]
    definition_extensions_filter = ['.max']

    def __init__(self, event_manager, parent=None):
        super(MaxQtOpenerClientWidget, self).__init__(
            event_manager, parent=parent or max_utils.get_main_window()
        )

        # Make sure we stays on top of Max
        self.setWindowFlags(QtCore.Qt.Tool)
