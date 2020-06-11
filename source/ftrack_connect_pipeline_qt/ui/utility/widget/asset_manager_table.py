# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack

from Qt import QtWidgets, QtCore

from ftrack_connect_pipeline_qt.ui.utility.model.asset_manager import AssetManagerModel
from ftrack_connect_pipeline_qt.ui.utility.delegate.asset_manager import (
    VersionDelegate
)


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