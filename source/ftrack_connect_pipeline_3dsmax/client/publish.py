# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

from ftrack_connect_pipeline.client.publish import QtPipelinePublishWidget
from qtpy import QtWidgets, QtCore
import MaxPlus

from ftrack_connect_pipeline_3dsmax.constants import HOST, UI


# TODO(spetterborg) Figure out whether we have one of these for max

class QtPipelineMaxPublishWidget(QtWidgets.QDockWidget, QtPipelinePublishWidget):
    '''Dockable maya load widget'''
    def __init__(self, hostid, parent=None):
        super(QtPipelineMaxPublishWidget, self).__init__(
            host=HOST, ui=UI, hostid=hostid, parent=parent
        )
        self.setWindowTitle('Max Pipeline Publisher')
        self.setObjectName('Max Pipeline Publisher')
        mainWindow = MaxPlus.GetQMaxMainWindow()
        mainWindow.addDockWidget(QtCore.Qt.LeftDockWidgetArea, self)
        self.setFloating(True)

    def show(self):
        super(QtPipelineMaxPublishWidget, self).show()
