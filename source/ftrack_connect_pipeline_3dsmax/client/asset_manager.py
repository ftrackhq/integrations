# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack

from Qt import QtCore, QtWidgets

from ftrack_connect_pipeline_qt.client.asset_manager import (
    QtAssetManagerClientWidget,
)
import ftrack_connect_pipeline.constants as constants
import ftrack_connect_pipeline_qt.constants as qt_constants
import ftrack_connect_pipeline_3dsmax.constants as max_constants


class MaxQtAssetManagerClientWidget(QtAssetManagerClientWidget):
    ui_types = [
        constants.UI_TYPE,
        qt_constants.UI_TYPE,
        max_constants.UI_TYPE,
    ]
    '''Dockable max asset manager widget'''

    def __init__(self, event_manager, asset_list_model, parent=None):
        self.dock_widget = QtWidgets.QDockWidget(parent=parent)
        super(MaxQtAssetManagerClientWidget, self).__init__(
            event_manager,
            asset_list_model,
            multithreading_enabled=False,
            parent=parent,
        )
        self.setWindowTitle('Max Pipeline Asset Manager')
        self.setObjectName('Max Pipeline Asset Manager')
        self.dock_widget.setWidget(self)
        parent.addDockWidget(QtCore.Qt.RightDockWidgetArea, self.dock_widget)
        self.dock_widget.setFloating(True)

    def show(self):
        self.dock_widget.show()
        super(MaxQtAssetManagerClientWidget, self).show()

    def get_theme_background_style(self):
        '''Override.'''
        return 'max'
