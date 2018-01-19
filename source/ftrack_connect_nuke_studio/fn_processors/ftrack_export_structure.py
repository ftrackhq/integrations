from QtExt import QtCore, QtWidgets

import os
from hiero.ui import ExportStructureViewer
from hiero.core import (
    ExportStructure2, 
    ExportStructureElement,
    TaskBase,
    TaskPresetBase,
    TaskPreset,
    RenderTaskPreset,
    TaskGroup,
    TaskData,
    FolderTask,
    FolderTaskPreset,
    TaskRegistry, 
    taskRegistry
)
from ftrack_base import FtrackBase


class FtrackProxyModel(QtCore.QSortFilterProxyModel):

  def __init__(self, parent=None):
    super(FtrackProxyModel, self).__init__(parent=parent)

  def data(self, index, role):
    result = super(FtrackProxyModel, self).data(index, role)
    print 'data in:',index, QtCore.Qt.ItemDataRole(role) , ' result:', result
    return result

  def columnCount(self, parent):
    result = super(FtrackProxyModel, self).columnCount(parent)
    print 'columnCount result:', result
    return result

  def rowCount(self, parent):
    result = super(FtrackProxyModel, self).rowCount(parent)
    print 'rowCount result:', result
    return result

  def index(self, row, column, parent=None):
    result = super(FtrackProxyModel, self).index(row, column, parent=parent)
    print 'index result:', result
    return result

  def children(self):
    result = super(FtrackProxyModel, self).children()
    print 'children result:', result
    return result


class FtrackExportStructureViewer(ExportStructureViewer, FtrackBase):

  def __init__(self, exportTemplate, structureViewerMode):
    ExportStructureViewer.__init__(self, exportTemplate, structureViewerMode)
    FtrackBase.__init__(self)
    self.logger.info('intializing FtrackExportStructureViewer')
    widget =  self.getWidget()

    tree = widget.findChild(QtWidgets.QTreeView)
    model = tree.model()

    self.proxy = FtrackProxyModel(self)
    self.proxy.setSourceModel(model)

    tree.setModel(self.proxy)
    tree.setSortingEnabled(True)


