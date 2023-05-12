# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack

from Qt import QtCore, QtWidgets

from framework_qt.client.asset_manager import (
    QtAssetManagerClientWidget,
)
import framework_core.constants as constants
import framework_qt.constants as qt_constants
import framework_3dsmax.constants as max_constants


class MaxQtAssetManagerClientWidget(QtAssetManagerClientWidget):
    ui_types = [
        constants.UI_TYPE,
        qt_constants.UI_TYPE,
        max_constants.UI_TYPE,
    ]
    '''Dockable max asset manager widget'''

    def __init__(self, event_manager, asset_list_model, parent=None):
        self.dock_widget = QtWidgets.QDockWidget(parent=parent)
        self.dock_widget.setWindowTitle('ftrack Pipeline Asset Manager')
        self.dock_widget.setObjectName('ftrack Pipeline Asset Manager')
        super(MaxQtAssetManagerClientWidget, self).__init__(
            event_manager,
            asset_list_model,
            multithreading_enabled=False,
            parent=parent,
        )
        self.dock_widget.setWidget(self)
        parent.addDockWidget(QtCore.Qt.RightDockWidgetArea, self.dock_widget)
        self.dock_widget.setFloating(False)

    def show(self):
        self.dock_widget.show()
        super(MaxQtAssetManagerClientWidget, self).show()

    def get_theme_background_style(self):
        '''Override.'''
        return 'max'
