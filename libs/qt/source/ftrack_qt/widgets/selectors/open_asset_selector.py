# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

import logging

from Qt import QtWidgets, QtCore, QtGui

from ftrack_qt.widgets.selectors.version_selector import VersionSelector
from ftrack_qt.widgets.thumbnails import OpenAssetVersionThumbnail

# TODO: add a reload button that emits a signal


class AssetListItemWidget(QtWidgets.QFrame):
    '''Widget representing an asset, with version selector, within the list,
    for user selection'''

    version_changed = QtCore.Signal(object)
    '''Signal emitted when version is changed, with assetversion entity as argument'''

    @property
    def enable_version_select(self):
        '''Return enable_version_select'''
        return True

    @property
    def version(self):
        if self._version_combobox:
            return self._version_combobox.version

    def __init__(self, asset_name, versions):
        '''Represent *asset* in list, with *session* for querying ftrack.
        If *fetch_assetversions* is given, user is presented a asset version
        selector. Otherwise, display latest version'''
        super(AssetListItemWidget, self).__init__()

        self._asset_name = asset_name
        self._versions = versions

        self._thumbnail_widget = None
        self._asset_name_widget = None
        self._create_label = None
        self._version_label = None
        self._version_combobox = None
        self._version_info_widget = None

        self._latest_version = None

        self.pre_build()
        self.build()
        self.post_build()

    def pre_build(self):
        self.setLayout(QtWidgets.QHBoxLayout())
        self.layout().setContentsMargins(0, 0, 0, 0)
        self.layout().setSpacing(5)

    def build(self):
        # TODO: implement thumbnail
        self._thumbnail_widget = OpenAssetVersionThumbnail()
        self._thumbnail_widget.setScaledContents(True)
        self._thumbnail_widget.setMinimumSize(57, 31)
        self._thumbnail_widget.setMaximumSize(57, 31)
        self.layout().addWidget(self._thumbnail_widget)

        self._asset_name_widget = QtWidgets.QLabel(self._asset_name)
        self.layout().addWidget(self._asset_name_widget)

        if self.enable_version_select:
            self._version_combobox = VersionSelector()
            self._version_combobox.set_versions(self._versions)
            self._version_combobox.setMaximumHeight(20)
            self.layout().addWidget(self._version_combobox)

            self._version_info_widget = QtWidgets.QLabel()
            self._version_info_widget.setObjectName('gray')
            self.layout().addWidget(self._version_info_widget, 10)

            # self._latest_version = self._version_combobox.set_asset_entity(
            #     self.asset
            # )

            # self._update_publisher_info(self._latest_version)
        # TODO: double check this
        # else:
        #     self._create_label = QtWidgets.QLabel('- create')
        #     self._create_label.setObjectName("gray")
        #     self.layout().addWidget(self._create_label)
        #
        #     self._version_label = QtWidgets.QLabel(
        #         'Version {}'.format(
        #             self.asset['latest_version']['version'] + 1
        #         )
        #     )
        #     self._version_label.setObjectName("color-primary")
        #     self.layout().addWidget(self._version_label)
        #
        #     self.layout().addStretch()
        #
        #     self.setToolTip(string_utils.str_context(self.asset['parent']))
        #
        #     self._latest_version = self.asset['latest_version']

        # if self._latest_version:
        self._thumbnail_widget.load(self._version_combobox.version['url'])
        #
        # self.setToolTip(string_utils.str_context(self.asset['parent']))

    def post_build(self):
        self._version_combobox.currentIndexChanged.connect(
            self._on_current_version_changed
        )

    def _on_current_version_changed(self, index):
        '''User has selected new version *assetversion_entity*, update the
        thumbnail and emit event'''
        version_dict = self._version_combobox.version()
        if version_dict:
            # TODO: reload thumbnail, updatePublisher_info?
            self.version_changed.emit(version_dict)

        #
        # if assetversion_entity:
        #     self._thumbnail_widget.load(assetversion_entity['id'])
        #     self._update_publisher_info(assetversion_entity)
        #     self.versionChanged.emit(assetversion_entity)
        # else:
        #     self._thumbnail_widget.use_placeholder()
        #     self._update_publisher_info(None)
        #     self.versionChanged.emit(None)

    # def _update_publisher_info(self, assetversion_entity):
    #     '''Update the publisher info widget with the *version_entity*'''
    #     if assetversion_entity:
    #         self._version_info_widget.setText(
    #             '{} {} @ {}'.format(
    #                 assetversion_entity['user']['first_name'],
    #                 assetversion_entity['user']['last_name'],
    #                 assetversion_entity['date'].strftime('%y-%m-%d %H:%M'),
    #             )
    #         )
    #     else:
    #         self._version_info_widget.setText('')


class AssetList(QtWidgets.QListWidget):
    '''Widget presenting list of existing assets'''

    version_changed = QtCore.Signal(object)
    '''Signal emitted when version is changed, with assetversion entity as 
    argument (version select mode)'''

    assets_added = QtCore.Signal(object)

    def __init__(self, parent=None):
        super(AssetList, self).__init__(parent=parent)
        self.logger = logging.getLogger(
            __name__ + '.' + self.__class__.__name__
        )

        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.setSpacing(1)
        self.assets = []

    def set_assets(self, assets):
        self.assets = assets

        for asset_id, asset_dict in self.assets.items():
            widget = AssetListItemWidget(
                asset_name=asset_dict['name'], versions=asset_dict['versions']
            )

            widget.version_changed.connect(self._on_version_changed_callback)
            list_item = QtWidgets.QListWidgetItem(self)
            list_item.setSizeHint(
                QtCore.QSize(
                    widget.sizeHint().width(), widget.sizeHint().height() + 5
                )
            )
            self.setItemWidget(list_item, widget)
            self.addItem(list_item)
        self.assets_added.emit(assets)

    def _on_version_changed_callback(self, version):
        self.version_changed.emit(version)


class AssetListAndInput(QtWidgets.QWidget):
    '''Compound widget containing asset list and new asset input'''

    def __init__(self, parent=None):
        super(AssetListAndInput, self).__init__(parent=parent)
        self.setLayout(QtWidgets.QVBoxLayout())
        self.layout().setContentsMargins(0, 0, 0, 0)
        self.layout().setSpacing(0)

    def add_asset_list(self, asset_list):
        '''Add *asset_list* widget to widget'''
        self._asset_list = asset_list
        self.layout().addWidget(asset_list)

    def resizeEvent(self, event):
        '''(Override)'''
        self.size_changed()

    def size_changed(self):
        '''Resize asset list to fit widget, to prevent unnecessary scrolling'''
        self._asset_list.setFixedSize(
            self.size().width() - 1,
            self._asset_list.sizeHintForRow(0) * self._asset_list.count()
            + 2 * self._asset_list.frameWidth(),
        )


class OpenAssetSelector(QtWidgets.QWidget):
    '''Widget for choosing an existing asset and asset version, or input asset
    name for creating a new asset, depending on mode.'''

    VALID_ASSET_NAME = QtCore.QRegExp('[A-Za-z0-9_]+')

    assets_added = QtCore.Signal(object)
    '''Signal emitted when assets are added, with list of asset entities as argument'''

    version_changed = QtCore.Signal(object)
    '''Signal emitted when version is changed, with assetversion entity as
    argument (version select mode)'''

    # TODO: double check if update_widget is needed and in case it is refactor it.
    # update_widget = QtCore.Signal(object)

    def __init__(
        self,
        parent=None,
    ):
        '''
        Initialise asset selector widget.

        :param mode: The mode of operation.
        :param fetch_assets: Callback to fetch assets
        :param session: ftrack session, required for thumbnail load.
        :param fetch_assetversions: Callback to fetch asset version for a specific
        asset.
        :param parent:
        '''
        super(OpenAssetSelector, self).__init__(parent=parent)
        self.logger = logging.getLogger(
            __name__ + '.' + self.__class__.__name__
        )

        self._list_and_input = None
        self._asset_list = None
        self._new_asset_input = None

        self._selected_index = None

        self.validator = QtGui.QRegExpValidator(self.VALID_ASSET_NAME)
        self.placeholder_name = "Asset Name..."

        self.pre_build()
        self.build()
        self.post_build()

    def pre_build(self):
        main_layout = QtWidgets.QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(main_layout)

    def build(self):
        self._list_and_input = AssetListAndInput()

        self._asset_list = AssetList()

        self._asset_list.setVisible(True)

        self._list_and_input.add_asset_list(self._asset_list)

        self.layout().addWidget(self._list_and_input)

    def post_build(self):
        self._asset_list.assets_added.connect(self._on_assets_added)
        self._asset_list.version_changed.connect(self._on_version_changed)
        # self.updateWidget.connect(self._update_widget)

    def _on_assets_added(self, assets):
        self.assets_added.emit(assets)

    def set_assets(self, assets):
        self._asset_list.set_assets(assets)

    def _on_version_changed(self, version):
        self.version_changed.emit(version)

    # def _pre_select_asset(self):
    #     '''Assets have been loaded, select most suitable asset to start with'''
    #     if self._asset_list.count() > 0:
    #         self._asset_list.setCurrentRow(0)
    #         self._asset_list.show()
    #     else:
    #         self._asset_list.hide()
    #     self._list_and_input.size_changed()
    #     self.assetsAdded.emit(self.assets)
