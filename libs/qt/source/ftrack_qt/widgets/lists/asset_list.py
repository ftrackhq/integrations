# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

import logging

from Qt import QtWidgets, QtCore, QtGui


class AssetList(QtWidgets.QListWidget):
    '''Widget presenting list of existing assets'''

    version_changed = QtCore.Signal(object)
    '''Signal emitted when version is changed, with assetversion entity as 
    argument (version select mode)'''

    assets_added = QtCore.Signal(object)
    '''Signal emitted when assets are added to the list'''

    selected_item_changed = QtCore.Signal(object, object, object)
    '''Signal emitted when selected item is changed with arguments containing 
    the index of the current version, the version dictionary and the asset_id'''

    def __init__(self, asset_list_widget_item, parent=None):
        '''Initialize AssetList'''
        super(AssetList, self).__init__(parent=parent)
        self.logger = logging.getLogger(
            __name__ + '.' + self.__class__.__name__
        )
        self.asset_list_widget_item = asset_list_widget_item

        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.setSpacing(1)
        self.assets = []
        self.currentItemChanged.connect(self._on_item_changed)

    def set_assets(self, assets):
        '''Set assets for the list'''
        self.assets = assets

        for asset_id, asset_dict in self.assets.items():
            widget = self.asset_list_widget_item(
                asset_name=asset_dict['name'],
                asset_id=asset_id,
                versions=asset_dict['versions'],
                server_url=asset_dict['server_url'],
            )

            if hasattr(widget, 'version_changed'):
                widget.version_changed.connect(
                    self._on_version_changed_callback
                )
            list_item = QtWidgets.QListWidgetItem(self)
            list_item.setSizeHint(
                QtCore.QSize(
                    widget.sizeHint().width(), widget.sizeHint().height() + 5
                )
            )
            if hasattr(widget, 'enable_version_select'):
                widget.enable_version_select = False
            self.setItemWidget(list_item, widget)
            self.addItem(list_item)
        self.assets_added.emit(assets)

    def _on_version_changed_callback(self, version):
        '''Handle version changed callback'''
        self.version_changed.emit(version)

    def _on_item_changed(self, current_item, previous_item):
        '''Handle item changed event'''
        if hasattr(self.itemWidget(current_item), 'enable_version_select'):
            if previous_item:
                self.itemWidget(previous_item).enable_version_select = False
            self.itemWidget(current_item).enable_version_select = True
        self.selected_item_changed.emit(
            self.indexFromItem(current_item),
            self.itemWidget(current_item).version,
            self.itemWidget(current_item).asset_id,
        )
