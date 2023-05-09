# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack
import logging

from Qt import QtWidgets, QtCore, QtGui

from ftrack_connect_pipeline import utils as core_utils

from ftrack_connect_pipeline_qt.utils import BaseThread
from ftrack_connect_pipeline_qt.ui.utility.widget import thumbnail
from ftrack_connect_pipeline_qt.ui.utility.widget.version_selector import (
    VersionComboBox,
)
from ftrack_connect_pipeline_qt.ui.utility.widget.busy_indicator import (
    BusyIndicator,
)


class AssetVersionListItem(QtWidgets.QFrame):
    '''Widget representing an asset and version selector within the asset list, for selecting'''

    versionChanged = QtCore.Signal(object)

    @property
    def latest_version(self):
        return self._latest_version

    def __init__(self, context_id, asset, session, filters=None):
        super(AssetVersionListItem, self).__init__()

        self.context_id = context_id
        self.asset = asset
        self.session = session
        self._filters = filters
        self._latest_version = None
        self.pre_build()
        self.build()
        self.post_build()

    def pre_build(self):
        self.setLayout(QtWidgets.QHBoxLayout())
        self.layout().setContentsMargins(1, 1, 1, 1)
        self.layout().setSpacing(3)

    def build(self):
        self.thumbnail_widget = thumbnail.AssetVersion(self.session)
        self.thumbnail_widget.setScaledContents(True)
        self.thumbnail_widget.setMinimumSize(46, 32)
        self.thumbnail_widget.setMaximumSize(46, 32)
        self.layout().addWidget(self.thumbnail_widget)

        asset_name_widget = QtWidgets.QLabel(self.asset['name'])
        self.layout().addWidget(asset_name_widget)

        self.version_combobox = VersionComboBox(
            self.session, filters=self._filters
        )
        self.version_combobox.set_context_id(self.context_id)
        self.version_combobox.setMaximumHeight(20)
        self.layout().addWidget(self.version_combobox)

        self._version_info_widget = QtWidgets.QLabel()
        self._version_info_widget.setObjectName('gray')
        self.layout().addWidget(self._version_info_widget, 10)

        self._latest_version = self.version_combobox.set_asset_entity(
            self.asset
        )
        self.current_version_id = self.current_version_number = None
        if self._latest_version:
            self.thumbnail_widget.load(self._latest_version['id'])
            self.current_version_id = self._latest_version['id']
            self.current_version_number = self._latest_version['version']
            self._update_publisher_info(self._latest_version)
        self.setToolTip(core_utils.str_context(self.asset['parent']))

    def post_build(self):
        self.version_combobox.versionChanged.connect(
            self._on_current_version_changed
        )
        self.version_combobox.filterMessage.connect(self._on_filter_message)

    def _on_current_version_changed(self, version_id):
        '''User has selected new version *version_id*, update the thumbnail and emit event'''
        if version_id:
            version = self.session.query(
                'AssetVersion where id={}'.format(version_id)
            ).one()
            self.current_version_number = version['version']
            self.current_version_id = version['id']
            self.thumbnail_widget.load(self.current_version_id)
            self._update_publisher_info(version)
            self.versionChanged.emit(self)
        else:
            self.current_version_number = -1
            self.current_version_id = None
            self.versionChanged.emit(None)

    def _on_filter_message(self, message):
        '''Update the widget with the *message* telling the reason for the version not be available'''
        self._version_info_widget.setText(message)

    def _update_publisher_info(self, version_entity):
        '''Update the publisher info widget with the *version_entity*'''
        self._version_info_widget.setText(
            '{} {} @ {}'.format(
                version_entity['user']['first_name'],
                version_entity['user']['last_name'],
                version_entity['date'].strftime('%y-%m-%d %H:%M'),
            )
        )


class AssetList(QtWidgets.QListWidget):
    '''Widget presenting list of existing assets'''

    assetsQueryDone = QtCore.Signal()
    assetsAdded = QtCore.Signal()
    versionChanged = QtCore.Signal(object)

    @property
    def widgets(self):
        '''Return list of widgets in list'''
        result = []
        for row in range(0, self.count()):
            result.append(self.itemWidget(self.item(row)))
        return result

    def __init__(
        self,
        session,
        filters=None,
        parent=None,
    ):
        super(AssetList, self).__init__(parent=parent)
        self.logger = logging.getLogger(
            __name__ + '.' + self.__class__.__name__
        )
        self.session = session
        self._filters = filters
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.horizontalScrollBar().setEnabled(False)
        self.verticalScrollBar().setEnabled(False)
        self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.setSpacing(1)
        self.assets = []

    def wheelEvent(self, event):
        '''(Override)'''
        event.ignore()

    def _query_assets_from_context_async(self, context_id, asset_type_name):
        '''(Run in background thread) Fetch assets from current context'''
        # TODO: Move this to plugin call so this can be customized
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
            'from Asset where (versions.task.id is {0} or versions.asset.parent.id is {0}) and type.id is {1}'.format(
                context_id, asset_type_entity['id']
            )
        ).all()

        return assets

    def _store_assets_async(self, assets):
        '''(Called from background thread) store assets and add through signal'''
        self.assets = assets
        # Add data placeholder for new asset input
        self.assetsQueryDone.emit()

    def rebuild(self):
        '''Add fetched assets to list'''
        self.clear()
        for asset_entity in self.assets:
            widget = AssetVersionListItem(
                self._context_id,
                asset_entity,
                self.session,
                filters=self._filters,
            )
            widget.versionChanged.connect(self._on_version_changed)
            list_item = QtWidgets.QListWidgetItem(self)
            list_item.setSizeHint(
                QtCore.QSize(
                    widget.sizeHint().width(),
                    widget.sizeHint().height() + 5,
                )
            )
            self.addItem(list_item)
            self.setItemWidget(list_item, widget)
        self.assetsAdded.emit()

    def on_context_changed(self, context_id, asset_type_name):
        '''The current context has changed to *context_id*, with *asset_type_name*. Rebuild the list accordingly.'''
        self.clear()
        thread = BaseThread(
            name='get_assets_thread',
            target=self._query_assets_from_context_async,
            callback=self._store_assets_async,
            target_args=(context_id, asset_type_name),
        )
        thread.start()

    def _on_version_changed(self, asset_item):
        '''User has selected a new version for *asset_item*, emit event'''
        self.versionChanged.emit(asset_item)

    def _size_changed(self):
        '''The size of list widget has changed, make sure to set fixed height to prevent unwanted padding'''
        self.setFixedHeight(
            self.sizeHintForRow(0) * self.count() + 20
        )  # Add some extra space to prevent unwanted scrolling


class AssetListSelector(QtWidgets.QFrame):
    '''Widget for selecting an asset version to open, presented as a list.'''

    valid_asset_name = QtCore.QRegExp('[A-Za-z0-9_]+')

    assetChanged = QtCore.Signal(object, object, object, object)

    def __init__(self, session, filters=None, parent=None):
        super(AssetListSelector, self).__init__(parent=parent)
        self._busy_widget = None
        self.logger = logging.getLogger(
            __name__ + '.' + self.__class__.__name__
        )

        self.session = session
        self._filters = filters

        self.pre_build()
        self.build()
        self.post_build()

    def pre_build(self):
        self.setLayout(QtWidgets.QVBoxLayout())
        self.layout().setContentsMargins(1, 1, 1, 1)
        self.layout().setSpacing(0)

    def build(self):
        self.asset_list = AssetList(
            self.session,
            filters=self._filters,
        )
        self.layout().addWidget(self.asset_list)
        self._busy_widget = BusyIndicator(start=False)
        self._busy_widget.setMinimumSize(QtCore.QSize(24, 24))
        self.layout().addWidget(self._busy_widget)
        self._busy_widget.setVisible(False)

    def post_build(self):
        self.asset_list.itemSelectionChanged.connect(self._list_item_changed)
        self.asset_list.versionChanged.connect(self._on_current_asset_changed)
        self.asset_list.assetsQueryDone.connect(self._rebuild)
        self.asset_list.assetsAdded.connect(self._pre_select_asset)

    def _rebuild(self):
        '''Add assets queried in separate thread to list'''
        self.asset_list.rebuild()
        self._busy_widget.stop()
        self._busy_widget.setVisible(False)
        self.asset_list.setVisible(True)

    def _pre_select_asset(self):
        '''Assets have been loaded, select most suitable asset to start with
        - have the most recent published version'''
        recent_version = None
        selected_index = -1
        for idx, widget in enumerate(self.asset_list.widgets):
            asset_latest_version = widget.latest_version
            if (
                recent_version is None
                or recent_version['date'] < asset_latest_version['date']
            ):
                recent_version = asset_latest_version
                selected_index = idx
        if selected_index > -1:
            self.asset_list.setCurrentRow(selected_index)
        self.asset_list._size_changed()

    def _list_item_changed(self):
        '''List row selection has changed, emit asset change event'''
        selected_index = self.asset_list.currentRow()
        if selected_index > -1:
            asset_widget = self.asset_list.itemWidget(
                self.asset_list.item(selected_index)
            )
            self._on_current_asset_changed(asset_widget)

    def _on_current_asset_changed(self, asset_widget):
        '''Asset identified by *asset_widget* has been selected.'''
        asset_entity = None
        if asset_widget:
            # A proper asset were selected
            asset_entity = asset_widget.asset
            if asset_widget.current_version_id:
                version_num = asset_widget.current_version_number
                self.assetChanged.emit(
                    asset_entity['name'] if asset_entity else None,
                    asset_entity,
                    asset_widget.current_version_id,
                    version_num,
                )
                return
        self.assetChanged.emit(
            asset_entity['name'] if asset_entity else None,
            asset_entity,
            None,
            None,
        )

    def set_context(self, context_id, asset_type_name):
        '''Set the new context to *context_id* with *asset_type_name*'''
        self.logger.debug('setting context to :{}'.format(context_id))
        self.asset_list.setVisible(False)
        self._busy_widget.start()
        self._busy_widget.setVisible(True)
        self.asset_list.on_context_changed(context_id, asset_type_name)

    def _get_context_entity(self, context_id):
        '''Get the context entity for *context_id*'''
        context_entity = self.session.query(
            'select name from Context where id is "{}"'.format(context_id)
        ).first()
        return context_entity
