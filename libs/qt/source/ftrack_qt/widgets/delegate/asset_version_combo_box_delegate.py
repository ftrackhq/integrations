# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

try:
    from PySide6 import QtWidgets, QtCore
except ImportError:
    from PySide2 import QtWidgets, QtCore, QtGui

# TODO: try to generalize this delegate to be able to pass the looking keys.
#  So it can be used in multiple places and not only for asset versions.


class AssetVersionComboBoxDelegate(QtWidgets.QStyledItemDelegate):
    '''
    QItemDelegate that provides a combo box to select versions of an
    asset_version
    '''

    index_changed = QtCore.Signal(object, object)

    def __init__(self, parent=None):
        super(AssetVersionComboBoxDelegate, self).__init__(parent=parent)

    def createEditor(self, parent, option, index):
        '''Creates the ComboBox'''
        item = index.model().data(index, index.model().DATA_ROLE)

        versions_collection = item['asset']['versions']
        combo = QtWidgets.QComboBox(parent)
        for asset_version in versions_collection:
            combo.addItem(str(asset_version['version']), asset_version)

        return combo

    def setEditorData(self, editor, index):
        '''Sets the given *data* into the given *editor*'''
        editor_data = str(index.model().data(index, QtCore.Qt.EditRole))
        idx = editor.findText(editor_data)
        editor.setCurrentIndex(idx)

    def setModelData(self, editor, model, index):
        '''
        Emits the signal index_changed when a new version is been selected
        '''
        index.data()
        if not index.isValid():
            return False
        data = editor.itemData(editor.currentIndex())
        if not data:
            return False
        self.index_changed.emit(index, data)
