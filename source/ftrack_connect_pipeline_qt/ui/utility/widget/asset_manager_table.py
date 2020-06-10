# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack

from Qt import QtWidgets, QtCore

from ftrack_connect_pipeline_qt.ui.utility.model.asset_manager import AssetManagerModel

class VersionDelegate(QtWidgets.QItemDelegate):

    def __init__(self, parent=None):
        super(VersionDelegate, self).__init__(parent=parent)

    def createEditor(self, parent, option, index):
        item = index.model().item(index)
        versions_collection = item.get_available_asset_versions()

        combo = QtWidgets.QComboBox(parent)
        for asset_version in versions_collection:
            combo.addItem(str(asset_version['version']), asset_version['id'])
            #TODO:pass the asset_version(ftrack object) as a role ftrack role
        combo.currentIndexChanged.connect(self.currentItemChanged)
        return combo

    def setEditorData(self, editor, index):
        editor.blockSignals(True)
        editor.setCurrentIndex(int(index.model().data(index)))
        editor.blockSignals(False)

    def setModelData(self, editor, model, index):
        model.setData(index, editor.itemData(editor.currentIndex()))

    @QtCore.Slot()
    def currentItemChanged(self):
        self.commitData.emit(self.sender())


class AssetManagerTableView(QtWidgets.QTableView):
    '''Model representing AssetManager.'''

    #: Signal when location changed.
    # locationChanged = QtCore.Signal()
    #
    # #: Signal when selection changes. Pass new selection.
    # selectionChanged = QtCore.Signal(object)

    def __init__(self, ftrack_asset_list, session, parent=None):
        '''Initialise browser with *root* entity.

        Use an empty *root* to start with list of projects.

        *parent* is the optional owner of this UI element.

        '''
        super(AssetManagerTableView, self).__init__(parent=parent)

        self.ftrack_asset_list = ftrack_asset_list

        self._session = session

        self.pre_build()
        self.build()
        self.post_build()

    def pre_build(self):
        pass

    def build(self):

        model = AssetManagerModel(
            ftrack_asset_list=self.ftrack_asset_list, parent=self
        )
        self.setModel(model)
        self.version_cb_delegate = VersionDelegate(self)
        self.setItemDelegateForColumn(
            model.get_version_column_idx(), self.version_cb_delegate
        )

    def post_build(self):
        '''Perform post-construction operations.'''
        pass