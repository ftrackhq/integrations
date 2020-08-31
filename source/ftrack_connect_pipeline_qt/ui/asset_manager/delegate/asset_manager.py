# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack

from Qt import QtWidgets, QtCore, QtGui
from ftrack_connect_pipeline.asset import asset_info

class VersionDelegate(QtWidgets.QItemDelegate):
    change_version = QtCore.Signal(object, object)

    def __init__(self, parent=None):
        super(VersionDelegate, self).__init__(parent=parent)

    def createEditor(self, parent, option, index):
        '''Creates the ComboBox'''

        # Initialize the ftrack info again as when quering from the
        # model even if the DATA_ROLE has the FtrackAssetInfo dictionary,
        # it returns a generic diccionary.
        item = asset_info.FtrackAssetInfo(index.model().data(index, index.model().DATA_ROLE))

        versions_collection = item['versions']
        combo = QtWidgets.QComboBox(parent)
        for asset_version in versions_collection:
            combo.addItem(str(asset_version['version']), asset_version['id'])

        return combo

    def setEditorData(self, editor, index):
        '''Sets the given *data* into the given *editor*'''
        editor_data = str(index.model().data(index, QtCore.Qt.EditRole))
        idx = editor.findText(editor_data)
        editor.setCurrentIndex(idx)

    def setModelData(self, editor, model, index):
        '''
        Emits the signal change_version when a new version is been selected
        '''
        if not index.isValid():
            return False
        self.change_version.emit(index, editor.itemData(editor.currentIndex()))
        # model.setData(
        #     index, editor.itemData(editor.currentIndex()), QtCore.Qt.EditRole
        # )

