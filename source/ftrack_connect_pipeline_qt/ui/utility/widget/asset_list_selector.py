# :coding: utf-8
# :copyright: Copyright (c) 2014-2021 ftrack
import logging
from functools import partial

from Qt import QtWidgets, QtCore, QtGui

from ftrack_connect_pipeline_qt.utils import BaseThread
from ftrack_connect_pipeline_qt.ui.utility.widget.thumbnail import AssetVersion
from ftrack_connect_pipeline_qt.utils import set_property
from ftrack_connect_pipeline_qt.ui.utility.widget.version_selector import (
    VersionComboBox,
)


class AssetVersionListItem(QtWidgets.QFrame):
    '''Widget representing an asset within the'''

    versionChanged = QtCore.Signal()

    def __init__(self, context_id, asset, session):
        super(AssetVersionListItem, self).__init__()

        self.context_id = context_id
        self.asset = asset
        self.session = session
        self.pre_build()
        self.build()
        self.post_build()

    def pre_build(self):
        self.setLayout(QtWidgets.QHBoxLayout())
        self.layout().setContentsMargins(1, 1, 1, 1)
        self.layout().setSpacing(3)

    def build(self):
        self.thumbnail_widget = AssetVersion(self.session)
        self.thumbnail_widget.setScaledContents(True)
        self.thumbnail_widget.setMinimumSize(46, 32)
        self.thumbnail_widget.setMaximumSize(46, 32)
        self.layout().addWidget(self.thumbnail_widget)
        self.thumbnail_widget.load(self.asset['latest_version']['id'])

        self.asset_name = QtWidgets.QLabel(self.asset['name'])
        self.layout().addWidget(self.asset_name)

        self.version_combobox = VersionComboBox(self.session)
        self.version_combobox.set_context_id(self.context_id)
        self.version_combobox.set_asset_entity(self.asset)
        self.version_combobox.setMaximumHeight(20)
        self.layout().addWidget(self.version_combobox)
        self.current_version_id = self.asset['latest_version']['id']
        self.current_version_number = self.asset['latest_version']['version']

        self.layout().addStretch()

    def post_build(self):
        self.version_combobox.currentIndexChanged.connect(
            self._current_version_changed
        )

    def _current_version_changed(self, current_Findex):
        if current_index == -1:
            return
        self.current_version_number = (
            self.version_combobox.currentText().split("Version ")[1]
        )
        current_idx = self.version_combobox.currentIndex()
        self.current_version_id = self.version_combobox.itemData(current_idx)
        self.thumbnail_widget.load(self.current_version_id)
        self.versionChanged.emit()


class AssetList(QtWidgets.QListWidget):
    '''Widget presenting list of existing assets'''

    assetsQueryDone = QtCore.Signal()
    assetsAdded = QtCore.Signal()
    versionChanged = QtCore.Signal(object)

    def __init__(self, session, parent=None):
        super(AssetList, self).__init__(parent=parent)
        self.logger = logging.getLogger(
            __name__ + '.' + self.__class__.__name__
        )

        self.session = session
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.setSpacing(1)
        self.assets = []

    def _query_assets_from_context(self, context_id, asset_type_name):
        '''(Run in background thread) Fetch assets from current context'''
        self._context_id = context_id
        self._asset_type_name = asset_type_name
        asset_type_entity = self.session.query(
            'select name from AssetType where short is "{}"'.format(
                asset_type_name
            )
        ).first()
        assets = self.session.query(
            'select name, versions.task.id, type.id, id, latest_version,'
            'latest_version.version, latest_version.date '
            'from Asset where versions.task.id is {} and type.id is {}'.format(
                context_id, asset_type_entity['id']
            )
        ).all()
        return assets

    def _store_assets(self, assets):
        '''Async, store assets and add through signal'''
        self.assets = assets
        # Add data placeholder for new asset input
        self.assetsQueryDone.emit()

    def refresh(self):
        '''Add fetched assets to list'''
        self.clear()
        for asset_entity in self.assets:
            widget = AssetVersionListItem(
                self._context_id,
                asset_entity,
                self.session,
            )
            widget.versionChanged.connect(
                partial(self._on_version_changed, widget)
            )
            list_item = QtWidgets.QListWidgetItem(self)
            list_item.setSizeHint(
                QtCore.QSize(
                    widget.sizeHint().width(), widget.sizeHint().height() + 5
                )
            )
            self.addItem(list_item)
            self.setItemWidget(list_item, widget)
        self.assetsAdded.emit()

    def on_context_changed(self, context_id, asset_type_name):
        self.clear()

        thread = BaseThread(
            name='get_assets_thread',
            target=self._query_assets_from_context,
            callback=self._store_assets,
            target_args=(context_id, asset_type_name),
        )
        thread.start()

    def _on_version_changed(self, asset_item):
        self.versionChanged.emit(asset_item)


class AssetListAndInput(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super(AssetListAndInput, self).__init__(parent=parent)
        self.setLayout(QtWidgets.QVBoxLayout())
        self.layout().setContentsMargins(0, 0, 0, 0)
        self.layout().setSpacing(0)

    def add_asset_list(self, asset_list):
        self.asset_list = asset_list
        self.layout().addWidget(asset_list)

    def resizeEvent(self, event):
        self._size_changed()

    def _size_changed(self):
        self.asset_list.setFixedSize(
            self.size().width() - 1,
            self.asset_list.sizeHintForRow(0) * self.asset_list.count()
            + 2 * self.asset_list.frameWidth(),
        )


class AssetListSelector(QtWidgets.QFrame):
    valid_asset_name = QtCore.QRegExp('[A-Za-z0-9_]+')

    assetChanged = QtCore.Signal(object, object, object, object)

    def __init__(self, session, is_loader=False, parent=None):
        super(AssetListSelector, self).__init__(parent=parent)
        self.logger = logging.getLogger(
            __name__ + '.' + self.__class__.__name__
        )

        self.is_loader = is_loader
        self.session = session

        self.pre_build()
        self.build()
        self.post_build()

    def pre_build(self):
        self.setLayout(QtWidgets.QVBoxLayout())
        self.layout().setContentsMargins(1, 1, 1, 1)
        self.layout().setSpacing(0)

    def build(self):

        self.list_and_input = AssetListAndInput()

        self.asset_list = AssetList(self.session)
        self.list_and_input.add_asset_list(self.asset_list)

        self.layout().addWidget(self.list_and_input)

    def post_build(self):
        self.asset_list.itemSelectionChanged.connect(self._list_item_changed)
        self.asset_list.versionChanged.connect(self._current_asset_changed)
        self.asset_list.assetsQueryDone.connect(self._refresh)
        self.asset_list.assetsAdded.connect(self._pre_select_asset)

    def _refresh(self):
        '''Add assets queried in separate thread to list.'''
        self.asset_list.refresh()

    def _pre_select_asset(self):
        '''Assets have been loaded, select most suitable asset to start with
        - have the most recent published version'''
        recent_version = None
        selected_index = -1
        for idx, asset in enumerate(self.asset_list.assets):
            if (
                recent_version is None
                or recent_version['date'] < asset['latest_version.date']
            ):
                recent_version = asset['latest_version']
                selected_index = idx
        if selected_index > -1:
            self.asset_list.setCurrentRow(selected_index)
        self.list_and_input._size_changed()

    def _list_item_changed(self):
        selected_index = self.asset_list.currentRow()
        if selected_index > -1:
            self._current_asset_changed(
                self.asset_list.itemWidget(
                    self.asset_list.item(selected_index)
                )
            )

    def _current_asset_changed(self, asset_item):
        '''An existing asset has been selected.'''
        if asset_item:
            # A proper asset were selected
            asset_entity = asset_item.asset
            asset_name = asset_entity['name']
            asset_version_id = asset_item.current_version_id
            version_num = asset_item.current_version_number
            self.assetChanged.emit(
                asset_name, asset_entity, asset_version_id, version_num
            )

    def set_context(self, context_id, asset_type_name):
        self.logger.debug('setting context to :{}'.format(context_id))
        self.asset_list.on_context_changed(context_id, asset_type_name)

    def _get_context_entity(self, context_id):
        context_entity = self.session.query(
            'select name from Context where id is "{}"'.format(context_id)
        ).first()
        return context_entity
