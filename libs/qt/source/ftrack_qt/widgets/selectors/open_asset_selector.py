# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

import logging

from Qt import QtWidgets, QtCore, QtGui

from ftrack_qt.widgets.selectors.version_selector import VersionSelector
from ftrack_qt.widgets.thumbnails import OpenAssetVersionThumbnail
from ftrack_qt.utils.widget import set_property

# TODO: add a reload button that emits a signal


class AssetListWidgetItem(QtWidgets.QFrame):
    '''Widget representing an asset, with version selector, within the list,
    for user selection'''

    version_changed = QtCore.Signal(object)
    '''Signal emitted when version is changed, with assetversion entity as argument'''

    @property
    def enable_version_select(self):
        '''Return enable_version_select'''
        return self._version_combobox.isEnabled()

    @enable_version_select.setter
    def enable_version_select(self, value):
        '''Return enable_version_select'''
        self._version_combobox.setEnabled(value)

    @property
    def version(self):
        if self._version_combobox:
            return self._version_combobox.version

    def __init__(self, asset_name, versions):
        '''Represent *asset* in list, with *session* for querying ftrack.
        If *fetch_assetversions* is given, user is presented a asset version
        selector. Otherwise, display latest version'''
        super(AssetListWidgetItem, self).__init__()

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
        self._thumbnail_widget = OpenAssetVersionThumbnail()
        self._thumbnail_widget.setScaledContents(True)
        self._thumbnail_widget.setMinimumSize(57, 31)
        self._thumbnail_widget.setMaximumSize(57, 31)
        self.layout().addWidget(self._thumbnail_widget)

        self._asset_name_widget = QtWidgets.QLabel(self._asset_name)
        self.layout().addWidget(self._asset_name_widget)

        self._version_combobox = VersionSelector()
        self._version_combobox.set_versions(self._versions)
        self._version_combobox.setMaximumHeight(20)
        self.layout().addWidget(self._version_combobox)

        self._version_info_widget = QtWidgets.QLabel()
        self._version_info_widget.setObjectName('gray')
        self.layout().addWidget(self._version_info_widget, 10)

        self._thumbnail_widget.set_server_url(
            self._version_combobox.version['server_url']
        )
        self._thumbnail_widget.load(
            self._version_combobox.version['thumbnail']
        )
        self._version_info_widget.setText(
            f"{self._version_combobox.version['user_first_name']} "
            f"{self._version_combobox.version['user_last_name']} @ "
            f"{self._version_combobox.version['date'].strftime('%y-%m-%d %H:%M')}"
        )

    def post_build(self):
        self._version_combobox.currentIndexChanged.connect(
            self._on_current_version_changed
        )

    def _on_current_version_changed(self, index):
        '''User has selected new version *assetversion_entity*, update the
        thumbnail and emit event'''
        version_dict = self._version_combobox.version
        if version_dict:
            self.version_changed.emit(version_dict)
            self._thumbnail_widget.load(
                self._version_combobox.version['thumbnail']
            )
            self._version_info_widget.setText(
                f"{self._version_combobox.version['user_first_name']} "
                f"{self._version_combobox.version['user_last_name']} @ "
                f"{self._version_combobox.version['date'].strftime('%y-%m-%d %H:%M')}"
            )


class AssetList(QtWidgets.QListWidget):
    '''Widget presenting list of existing assets'''

    version_changed = QtCore.Signal(object)
    '''Signal emitted when version is changed, with assetversion entity as 
    argument (version select mode)'''

    assets_added = QtCore.Signal(object)

    selected_item_changed = QtCore.Signal(object, object)

    def __init__(self, parent=None):
        super(AssetList, self).__init__(parent=parent)
        self.logger = logging.getLogger(
            __name__ + '.' + self.__class__.__name__
        )

        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.setSpacing(1)
        self.assets = []
        self.currentItemChanged.connect(self._on_item_changed)

    def set_assets(self, assets):
        self.assets = assets

        for asset_id, asset_dict in self.assets.items():
            widget = AssetListWidgetItem(
                asset_name=asset_dict['name'], versions=asset_dict['versions']
            )

            widget.version_changed.connect(self._on_version_changed_callback)
            list_item = QtWidgets.QListWidgetItem(self)
            list_item.setSizeHint(
                QtCore.QSize(
                    widget.sizeHint().width(), widget.sizeHint().height() + 5
                )
            )
            widget.enable_version_select = False
            self.setItemWidget(list_item, widget)
            self.addItem(list_item)
        self.assets_added.emit(assets)

    def _on_version_changed_callback(self, version):
        self.version_changed.emit(version)

    def _on_item_changed(self, current_item, previous_item):
        if previous_item:
            self.itemWidget(previous_item).enable_version_select = False
        self.itemWidget(current_item).enable_version_select = True
        self.selected_item_changed.emit(
            self.indexFromItem(current_item),
            self.itemWidget(current_item).version,
        )


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

    selected_item_changed = QtCore.Signal(object)
    '''Signal emitted when an item is selected, with asset_version id
    argument'''

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

        self.selected_index = None

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

        self._list_and_input.add_asset_list(self._asset_list)

        self.layout().addWidget(self._list_and_input)

    def post_build(self):
        self._asset_list.assets_added.connect(self._on_assets_added)
        self._asset_list.version_changed.connect(self._on_version_changed)
        self._asset_list.selected_item_changed.connect(
            self._on_selected_item_changed
        )

    def _on_assets_added(self, assets):
        self.assets_added.emit(assets)

    def set_assets(self, assets):
        if not assets:
            self._asset_list.hide()
        else:
            self._asset_list.show()
        self._asset_list.set_assets(assets)

    def _on_version_changed(self, version):
        self.version_changed.emit(version)

    def _on_selected_item_changed(self, index, version):
        self.selected_index = index
        self.selected_item_changed.emit(version)


class NewAssetInput(QtWidgets.QFrame):
    '''Widget holding new asset input during publish'''

    text_changed = QtCore.Signal(object)

    def __init__(self, validator, placeholder_name):
        super(NewAssetInput, self).__init__()

        self._validator = validator
        self._placeholder_name = placeholder_name

        self.pre_build()
        self.build()
        self.post_build()

    def pre_build(self):
        self.setLayout(QtWidgets.QHBoxLayout())
        self.layout().setContentsMargins(4, 1, 1, 1)
        self.layout().setSpacing(1)
        self.setMaximumHeight(32)

    def build(self):
        self.button = QtWidgets.QPushButton('NEW')
        self.button.setStyleSheet('background: #FFDD86;')
        self.button.setFixedSize(56, 30)
        self.button.setMaximumSize(56, 30)

        self.layout().addWidget(self.button)

        self.name = QtWidgets.QLineEdit()
        self.name.setPlaceholderText(self._placeholder_name)
        self.name.setValidator(self._validator)
        self.name.setSizePolicy(
            QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Minimum
        )
        self.layout().addWidget(self.name, 1000)

        self.version_label = QtWidgets.QLabel('- Version 1')
        self.version_label.setObjectName("color-primary")
        self.layout().addWidget(self.version_label)

    def post_build(self):
        self.button.clicked.connect(self.input_clicked)
        self.name.mousePressEvent = self.input_clicked
        self.name.textChanged.connect(self.on_text_changed)

    def mousePressEvent(self, event):
        '''Override mouse press to emit signal'''
        self.text_changed.emit(self.name.text())

    def input_clicked(self, event):
        '''Callback on user button or name click'''
        self.text_changed.emit(self.name.text())

    def on_text_changed(self):
        self.text_changed.emit(self.name.text())


class PublishAssetSelector(OpenAssetSelector):
    '''Widget for choosing an existing asset and asset version, or input asset
    name for creating a new asset, depending on mode.'''

    VALID_ASSET_NAME = QtCore.QRegExp('[A-Za-z0-9_]+')

    new_asset = QtCore.Signal(object)

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
        self.validator = QtGui.QRegExpValidator(self.VALID_ASSET_NAME)
        self.placeholder_name = "Asset Name..."

        super(PublishAssetSelector, self).__init__(parent=parent)

    def build(self):
        super(PublishAssetSelector, self).build()

        # Create new asset
        self._new_asset_input = NewAssetInput(
            self.validator, self.placeholder_name
        )
        self._list_and_input.layout().addWidget(self._new_asset_input)

    def post_build(self):
        super(PublishAssetSelector, self).post_build()
        self._new_asset_input.text_changed.connect(self._on_new_asset)

    def _on_new_asset(self, asset_name):
        '''New asset name text changed'''
        self.selected_index = None
        self.selected_item_changed.emit(None)
        is_valid_name = self.validate_name(asset_name)
        if is_valid_name:
            self.new_asset.emit(asset_name)
        else:
            self.new_asset.emit(None)

    def validate_name(self, asset_name):
        '''Return True if *asset_name* is valid, also reflect this on input style'''
        is_valid_bool = True
        # Already an asset by that name
        if self._asset_list.assets:
            for asset_id, asset_dict in self._asset_list.assets.items():
                if asset_dict['name'].lower() == asset_name.lower():
                    is_valid_bool = False
                    break
        if is_valid_bool and self.validator:
            is_valid = self.validator.validate(asset_name, 0)
            if is_valid[0] != QtGui.QValidator.Acceptable:
                is_valid_bool = False
            else:
                is_valid_bool = True
        if is_valid_bool:
            set_property(self._new_asset_input.name, 'input', '')
        else:
            set_property(self._new_asset_input.name, 'input', 'invalid')
        return is_valid_bool
