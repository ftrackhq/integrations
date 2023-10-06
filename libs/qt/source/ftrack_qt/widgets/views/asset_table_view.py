# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

from Qt import QtWidgets, QtCore, QtGui

from ftrack_qt.widgets.models import AssetTableModel
from ftrack_qt.widgets.delegate import AssetVersionComboBoxDelegate


class AssetTableView(QtWidgets.QTableView):
    '''Table view representing an asset version.'''

    def __init__(self, column_mapping=None, parent=None):
        '''Initialise AssetManagerTableView with *event_manager*

        *event_manager* should be the
        :class:`ftrack_connect_pipeline.event.EventManager` instance to
        communicate to the event server.
        '''
        super(AssetTableView, self).__init__(parent=parent)

        self._column_mapping = column_mapping
        self._asset_model = None
        self._version_cb_delegate = None

        self.pre_build()
        self.build()
        self.post_build()

    def pre_build(self):
        '''Prepare general layout.'''
        self.setAlternatingRowColors(True)

        self.verticalHeader().hide()

        self.setSelectionBehavior(
            QtWidgets.QAbstractItemView.SelectRows
        )

        self.horizontalHeader().setStretchLastSection(True)

    def build(self):
        '''Build widgets and parent them.'''
        self._asset_model = AssetTableModel(
            column_mapping=self._column_mapping, parent=self
        )

        self.setModel(self._asset_model)
        self._version_cb_delegate = AssetVersionComboBoxDelegate(self)

        version_column_index = self._asset_model.headers.index('version')

        self.setItemDelegateForColumn(
            version_column_index, self._version_cb_delegate
        )
        self._asset_model.set_editable_column(version_column_index)

    def post_build(self):
        '''Perform post-construction operations.'''
        self._version_cb_delegate.index_changed.connect(
            self._on_asset_change_version
        )

    def _on_asset_change_version(self, index, value):
        self._asset_model.data_items[index.row()] = value

    def set_data_items(self, data_items):
        '''
        Sets the :obj:`data_items` with the given *data_items*
        '''
        self._asset_model.set_data_items(data_items)

    def _on_select_assets(self):
        selected_assets = []
        index_list = self.selectionModel().selectedRows()
        for index in index_list:
            selected_assets.append(
                self.model().data(index, self.model().DATA_ROLE)
            )
        return selected_assets


