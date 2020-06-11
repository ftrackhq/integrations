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

        combo.installEventFilter(self)
        return combo

    def setEditorData(self, editor, index):
        editor.blockSignals(True)
        editor_data = int(index.model().data(index, QtCore.Qt.EditRole))
        editor.setCurrentIndex(
            editor_data
        )
        editor.blockSignals(False)

    def setModelData(self, editor, model, index):
        if not index.isValid():
            return False

        model.setData(
            index, editor.itemData(editor.currentIndex()), QtCore.Qt.EditRole
        )

    @QtCore.Slot()
    def currentItemChanged(self):
        self.commitData.emit(self.sender())

