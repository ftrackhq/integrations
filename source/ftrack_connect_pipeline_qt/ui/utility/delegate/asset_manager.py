# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack

from Qt import QtWidgets, QtCore, QtGui

class VersionDelegate(QtWidgets.QItemDelegate):

    def __init__(self, parent=None):
        super(VersionDelegate, self).__init__(parent=parent)

    def createEditor(self, parent, option, index):
        item = index.model().ftrack_asset_list[index.row()]
        versions_collection = item.asset_versions

        combo = QtWidgets.QComboBox(parent)
        for asset_version in versions_collection:
            combo.addItem(str(asset_version['version']), asset_version['id'])
            #TODO:pass the asset_version(ftrack object) as a role ftrack role
        combo.currentIndexChanged.connect(self.currentItemChanged)
        return combo

    def setEditorData(self, editor, index):
        print "index --> {}".format(index)
        print "setting editor data"
        editor.blockSignals(True)
        editor.setCurrentIndex(
            int(index.model().data(index, QtCore.Qt.EditRole))
        )
        editor.blockSignals(False)

    def setModelData(self, editor, model, index):
        model.setData(
            index, editor.itemData(editor.currentIndex()), QtCore.Qt.EditRole
        )

    @QtCore.Slot()
    def currentItemChanged(self):
        self.commitData.emit(self.sender())

