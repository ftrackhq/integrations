# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack
import logging
import time
from functools import partial

from Qt import QtWidgets, QtCore, QtGui

from ftrack_connect_pipeline_qt.utils import BaseThread
from ftrack_connect_pipeline_qt.ui.utility.widget.thumbnail import (
    AssetVersion as AssetVersionThumbnail,
)
from ftrack_connect_pipeline_qt.ui.utility.widget.version_selector import (
    VersionComboBox,
)


class AssetItem(QtWidgets.QPushButton):
    '''An asset item within the grid'''

    versionChanged = QtCore.Signal(
        object, object
    )  # User commands a change of version

    def __init__(self, session, asset, context_id, parent=None):
        '''
        Initialize item

        :param session: :class:`ftrack_api.session.Session`
        :param asset: The asset entity
        :param context_id: Id of context
        :param parent: The parent dialog or frame
        '''
        super(AssetItem, self).__init__(parent=parent)
        self.logger = logging.getLogger(
            __name__ + '.' + self.__class__.__name__
        )
        self.setCheckable(True)
        self.setAutoExclusive(True)

        self.session = session
        self.asset = asset
        self.current_version_id = asset['latest_version']['id']
        self.context_id = context_id
        self.current_version_number = asset['latest_version']['version']

        self.pre_build()
        self.build()
        self.post_build()

    def pre_build(self):
        self.setLayout(QtWidgets.QVBoxLayout())
        self.layout().setContentsMargins(5, 2, 5, 1)
        self.setMinimumHeight(100)
        self.setMaximumHeight(100)
        self.setMinimumWidth(100)
        self.setMaximumWidth(100)

    def build(self):
        self.thumbnail_widget = AssetVersionThumbnail(self.session)
        self.thumbnail_widget.setScaledContents(True)
        self.thumbnail_widget.load(self.current_version_id)

        self.asset_name_label = QtWidgets.QLabel(self.asset['name'])
        self.asset_name_label.setObjectName('h3')
        self.version_combobox = VersionComboBox(self.session)
        self.version_combobox.set_context_id(self.context_id)
        self.version_combobox.set_asset_entity(self.asset)
        self.current_version_number = (
            self.version_combobox.currentText().split("v")[1]
        )

        self.layout().addWidget(self.thumbnail_widget, stretch=2)
        self.layout().addWidget(self.asset_name_label)
        self.layout().addWidget(self.version_combobox)

    def post_build(self):
        self.version_combobox.currentIndexChanged.connect(
            self._on_version_changed
        )

    def _on_version_changed(self, current_index):
        '''User has commanded change a version, propagate'''
        if current_index == -1:
            return
        self.current_version_number = (
            self.version_combobox.currentText().split("v")[1]
        )
        current_idx = self.version_combobox.currentIndex()
        self.current_version_id = self.version_combobox.itemData(current_idx)
        self.thumbnail_widget.load(self.current_version_id)
        self.versionChanged.emit(
            self.current_version_number, self.current_version_id
        )


class AssetGridSelector(QtWidgets.QWidget):
    '''Widget displaying assets (versions) in a grid, allowing user selection'''

    MAX_COLUMNS = 4

    assetChanged = QtCore.Signal(object, object, object, object)
    assetsQueryDone = QtCore.Signal(object)

    def __init__(self, session, parent=None):
        super(AssetGridSelector, self).__init__(parent=parent)
        self.logger = logging.getLogger(
            __name__ + '.' + self.__class__.__name__
        )

        self.session = session
        self.context_id = None

        self.pre_build()
        self.build()
        self.post_build()

    def pre_build(self):
        main_layout = QtWidgets.QGridLayout()
        main_layout.setContentsMargins(1, 1, 1, 1)
        self.setLayout(main_layout)

    def build(self):
        pass

    def post_build(self):
        self.assetsQueryDone.connect(self.add_items)

    def _pre_select_asset(self, asset_item):
        asset_item.click()

    def set_context(self, context_id, asset_type_name):
        self.logger.debug('setting context to :{}'.format(context_id))
        self.context_id = context_id
        self._asset_type_name = asset_type_name
        self._on_context_changed(context_id, asset_type_name)

    def clear_layout(self):
        while self.layout().count():
            child = self.layout().takeAt(0)
            if child.widget():
                child.widget().deleteLater()

    def _on_context_changed(self, context_id, asset_type_name):
        '''React upon context change, fetch assets (and versions) in the background'''
        self.clear_layout()

        thread = BaseThread(
            name='get_assets_thread',
            target=self.query_assets_from_context,
            callback=self.add_assets_to_ui,
            target_args=(context_id, asset_type_name),
        )
        thread.start()

    def query_assets_from_context(self, context_id, asset_type_name):
        '''(Run in background) Query assets and versions from context'''
        asset_type_entity = self.session.query(
            'select name from AssetType where short is "{}"'.format(
                asset_type_name
            )
        ).first()
        assets = self.session.query(
            'select name, type.id, id, latest_version, '
            'latest_version.id, latest_version.version '
            'from Asset where versions.task.id is {} and type.id is {}'.format(
                context_id, asset_type_entity['id']
            )
        ).all()

        return assets

    def add_assets_to_ui(self, assets):
        '''Assets have been queried, propaget to QT foreground thread'''
        self.assetsQueryDone.emit(assets)

    def add_items(self, assets):
        '''Add fetched assets to widget'''
        if 0 < len(assets):
            row = 0
            column = 0
            for asset in assets:
                asset_item = AssetItem(self.session, asset, self.context_id)
                asset_item.clicked.connect(
                    partial(self._on_asset_changed, asset_item)
                )
                asset_item.versionChanged.connect(
                    partial(self._on_version_changed, asset_item)
                )
                if row == 0 and column == 0:
                    self._pre_select_asset(asset_item)

                self.layout().addWidget(asset_item, row, column)
                if column == self.MAX_COLUMNS - 1:
                    row += 1
                    column = 0
                else:
                    column += 1
            while column < self.MAX_COLUMNS - 1:
                filler_label = QtWidgets.QLabel()
                filler_label.setMinimumWidth(130)
                self.layout().addWidget(filler_label, row, column)
                column += 1
        else:
            self.layout().addWidget(
                QtWidgets.QLabel(
                    '<html><i>No version(s) having "{}" assets published at this context!'
                    '</i></html>'.format(self._asset_type_name)
                ),
                0,
                0,
            )

    def _on_asset_changed(self, asset_item):
        '''User has selected another asset, evaluate and propagate'''
        self.current_asset_entity = asset_item.asset
        asset_name = asset_item.asset['name']
        asset_version_id = asset_item.current_version_id
        version_num = asset_item.current_version_number
        self.assetChanged.emit(
            asset_name,
            self.current_asset_entity,
            asset_version_id,
            version_num,
        )

    def _on_version_changed(self, asset_item, version_num, current_version_id):
        '''Version has been changed by user on an item, propagate'''
        if asset_item.asset != self.current_asset_entity:
            return
        self._on_asset_changed(asset_item)
