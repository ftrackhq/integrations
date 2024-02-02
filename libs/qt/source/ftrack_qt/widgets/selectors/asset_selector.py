# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

import logging

from Qt import QtWidgets, QtCore, QtGui

from ftrack_qt.widgets.frames import (
    AssetVersionCreation,
    AssetVersionSelection,
    NewAssetInput,
)
from ftrack_qt.widgets.lists import AssetList


class OpenAssetSelector(QtWidgets.QWidget):
    '''This widget allows the user to select an existing asset and asset version,
    or input an asset name for creating a new asset, depending on the mode.'''

    assets_added = QtCore.Signal(object)
    '''This signal is emitted when assets are added. It sends a list of assets 
    dictionaries as an argument'''

    version_changed = QtCore.Signal(object)
    '''This signal is emitted when the version is changed. It sends the version 
    number as an argument '''

    selected_item_changed = QtCore.Signal(object, object)
    '''This signal is emitted when an item is selected. It sends the version 
    dictionary as an argument and the asset id'''

    def __init__(
        self,
        parent=None,
    ):
        '''
        This method initialises the asset selector widget.
        '''
        super(OpenAssetSelector, self).__init__(parent=parent)
        self.logger = logging.getLogger(
            __name__ + '.' + self.__class__.__name__
        )

        self._list_and_input = None
        self._asset_list = None
        self._new_asset_input = None

        self.selected_index = None

        self.pre_build()
        self.build()
        self.post_build()

    def pre_build(self):
        '''This method sets up the main layout for the widget.'''
        main_layout = QtWidgets.QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(main_layout)

    def build(self):
        '''This method builds the asset list and adds it to the layout.'''

        self._asset_list = AssetList(AssetVersionSelection)

        self.layout().addWidget(self._asset_list)

    def post_build(self):
        '''This method connects signals to slots after building the widget.'''
        self._asset_list.assets_added.connect(self._on_assets_added)
        self._asset_list.version_changed.connect(self._on_version_changed)
        self._asset_list.selected_item_changed.connect(
            self._on_selected_item_changed
        )

    def _on_assets_added(self, assets):
        '''This method emits the assets_added signal with the given assets.'''
        self.assets_added.emit(assets)

    def set_assets(self, assets):
        '''This method sets the assets in the asset list and shows or hides it
        based on the presence of assets.'''
        if not assets:
            self._asset_list.hide()
        else:
            self._asset_list.show()
        self._asset_list.set_assets(assets)

    def _on_version_changed(self, version):
        '''This method emits the version_changed signal with the given version.'''
        self.version_changed.emit(version)

    def _on_selected_item_changed(self, index, version, asset_id):
        '''This method updates the selected index and emits the
        selected_item_changed signal with the given version.'''
        self.selected_index = index
        self.selected_item_changed.emit(version, asset_id)


class PublishAssetSelector(OpenAssetSelector):
    '''This widget allows the user to select an existing asset and asset version,
    or input an asset name for creating a new asset.'''

    VALID_ASSET_NAME = QtCore.QRegExp('[A-Za-z0-9_]+')

    new_asset = QtCore.Signal(object)
    '''This signal is emitted when a new asset is selected. It sends the
    new asset_name as argument.'''

    def __init__(
        self,
        parent=None,
    ):
        '''
        This method initialises the asset selector widget.
        '''
        self.validator = QtGui.QRegExpValidator(self.VALID_ASSET_NAME)
        self.placeholder_name = "Asset Name..."

        super(PublishAssetSelector, self).__init__(parent=parent)

    def build(self):
        '''This method builds the asset list and new asset input and adds them
        to the layout.'''
        self._list_and_input = AssetListAndInput()

        self._asset_list = AssetList(AssetVersionCreation)

        self._list_and_input.add_asset_list(self._asset_list)

        # Create new asset
        self._new_asset_input = NewAssetInput(
            self.validator, self.placeholder_name
        )
        self._list_and_input.add_asset_input(self._new_asset_input)

        self.layout().addWidget(self._list_and_input)

    def post_build(self):
        '''This method connects signals to slots after building the widget.'''
        super(PublishAssetSelector, self).post_build()
        self._new_asset_input.text_changed.connect(self._on_new_asset)

    def _on_new_asset(self, asset_name):
        '''This method handles changes to the new asset name input.'''
        self._asset_list.blockSignals(True)
        self._asset_list.setCurrentRow(-1)  # Make sure list is deselected
        self._asset_list.blockSignals(False)
        self.selected_index = None
        self.selected_item_changed.emit(None, None)
        is_valid_name = self.validate_name(asset_name)
        if is_valid_name:
            self.new_asset.emit(asset_name)
        else:
            self.new_asset.emit(None)

    def validate_name(self, asset_name):
        '''This method validates the given asset name and updates the input style.'''
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
        self._new_asset_input.set_valid(is_valid_bool)
        return is_valid_bool

    def set_default_new_asset_name(self, name):
        '''This method sets the default name for the new asset input.'''
        self._new_asset_input.set_default_name(name)

    def set_assets(self, assets):
        super(PublishAssetSelector, self).set_assets(assets)
        # Make sure widget expands properly to fit list
        self._list_and_input.size_changed()


class AssetListAndInput(QtWidgets.QWidget):
    '''This is a compound widget containing an asset list and a new asset input'''

    def __init__(self, parent=None):
        '''This method initializes the widget with a vertical layout.'''
        super(AssetListAndInput, self).__init__(parent=parent)
        self.setLayout(QtWidgets.QVBoxLayout())
        self.layout().setContentsMargins(0, 0, 0, 0)
        self.layout().setSpacing(0)
        self._asset_list = None
        self._asset_input = None

    def add_asset_list(self, asset_list):
        '''This method adds the given asset list to the widget.'''
        self._asset_list = asset_list
        self.layout().addWidget(asset_list)

    def add_asset_input(self, asset_input):
        '''This method adds the given asset input to the widget.'''
        self._asset_input = asset_input
        self.layout().addWidget(asset_input)

    def resizeEvent(self, event):
        '''This method overrides the resize event to handle size changes.'''
        self.size_changed()

    def size_changed(self):
        '''This method resizes the asset list to fit the widget, preventing
        unnecessary scrolling.'''
        self._asset_list.setFixedSize(
            self.size().width() - 1,
            self._asset_list.sizeHintForRow(0) * self._asset_list.count()
            + 2 * self._asset_list.frameWidth(),
        )
