# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

# TODO: review this code

import logging

from Qt import QtWidgets, QtCore, QtGui

import ftrack_utils.string as string_utils

from ftrack_utils.threading import BaseThread
import ftrack_qt
from ftrack_qt.widgets.thumbnails import AssetVersionThumbnail
from ftrack_qt.utils.widget import set_property


class AssetListItem(QtWidgets.QFrame):
    '''Widget representing an asset within the list, for user selection'''

    versionChanged = QtCore.Signal(object)
    '''Signal emitted when version is changed, with assetversion entity as argument'''

    @property
    def asset(self):
        '''Return asset entity'''
        return self._asset

    @property
    def session(self):
        '''Return session'''
        return self._session

    @property
    def enable_version_select(self):
        '''Return enable_version_select'''
        return self._fetch_assetversions is not None

    def __init__(self, asset, session, fetch_assetversions=None):
        '''Represent *asset* in list, with *session* for querying ftrack.
        If *fetch_assetversions* is given, user is presented a asset version
        selector. Otherwise, display latest version'''
        super(AssetListItem, self).__init__()

        self._asset = asset
        self._session = session
        self._fetch_assetversions = fetch_assetversions

        self._thumbnail_widget = None
        self._asset_name_widget = None
        self._asset_name = None
        self._create_label = None
        self._version_label = None
        self._version_combobox = None
        self._version_info_widget = None

        self._latest_version = None
        self._current_version_id = None
        self._current_version_number = None

        self.pre_build()
        self.build()
        self.post_build()

    def pre_build(self):
        self.setLayout(QtWidgets.QHBoxLayout())
        self.layout().setContentsMargins(0, 0, 0, 0)
        self.layout().setSpacing(5)

    def build(self):
        self._thumbnail_widget = AssetVersionThumbnail(self._session)
        self._thumbnail_widget.setScaledContents(True)
        self._thumbnail_widget.setMinimumSize(57, 31)
        self._thumbnail_widget.setMaximumSize(57, 31)
        self.layout().addWidget(self._thumbnail_widget)

        self._asset_name_widget = QtWidgets.QLabel(self.asset['name'])
        self.layout().addWidget(self._asset_name_widget)

        if self.enable_version_select:
            self._version_combobox = (
                ftrack_qt.widgets.selectors.VersionSelector(
                    self._fetch_assetversions
                )
            )
            self._version_combobox.set_context_id(self.context_id)
            self._version_combobox.setMaximumHeight(20)
            self.layout().addWidget(self._version_combobox)

            self._version_info_widget = QtWidgets.QLabel()
            self._version_info_widget.setObjectName('gray')
            self.layout().addWidget(self._version_info_widget, 10)

            self._latest_version = self._version_combobox.set_asset_entity(
                self.asset
            )

            self._update_publisher_info(self._latest_version)

        else:
            self._create_label = QtWidgets.QLabel('- create')
            self._create_label.setObjectName("gray")
            self.layout().addWidget(self._create_label)

            self._version_label = QtWidgets.QLabel(
                'Version {}'.format(
                    self.asset['latest_version']['version'] + 1
                )
            )
            self._version_label.setObjectName("color-primary")
            self.layout().addWidget(self._version_label)

            self.layout().addStretch()

            self.setToolTip(string_utils.str_context(self.asset['parent']))

            self._latest_version = self.asset['latest_version']

        if self._latest_version:
            self._thumbnail_widget.load(self._latest_version['id'])
            self._current_version_id = self._latest_version['id']
            self._current_version_number = self._latest_version['version']

        self.setToolTip(string_utils.str_context(self.asset['parent']))

    def post_build(self):
        if self._version_combobox:
            self._version_combobox.versionChanged.connect(
                self._on_current_version_changed
            )

    def _on_current_version_changed(self, assetversion_entity):
        '''User has selected new version *assetversion_entity*, update the
        thumbnail and emit event'''
        if assetversion_entity:
            self.thumbnail_widget.load(assetversion_entity['id'])
            self._update_publisher_info(assetversion_entity)
            self.versionChanged.emit(assetversion_entity)
        else:
            self.thumbnail_widget.use_placeholder()
            self._update_publisher_info(None)
            self.versionChanged.emit(None)

    def _update_publisher_info(self, assetversion_entity):
        '''Update the publisher info widget with the *version_entity*'''
        if assetversion_entity:
            self._version_info_widget.setText(
                '{} {} @ {}'.format(
                    assetversion_entity['user']['first_name'],
                    assetversion_entity['user']['last_name'],
                    assetversion_entity['date'].strftime('%y-%m-%d %H:%M'),
                )
            )
        else:
            self._version_info_widget.setText('')


class AssetList(QtWidgets.QListWidget):
    '''Widget presenting list of existing assets'''

    versionChanged = QtCore.Signal(object)
    '''Signal emitted when version is changed, with assetversion entity as 
    argument (version select mode)'''

    assetsQueryDone = QtCore.Signal()  # Assets have been queried from ftrack
    assetsAdded = QtCore.Signal()  # Assets have been added to the widget

    @property
    def session(self):
        '''Return session'''
        return self._session

    def __init__(
        self, fetch_assets, fetch_assetversions, session, parent=None
    ):
        super(AssetList, self).__init__(parent=parent)
        self.logger = logging.getLogger(
            __name__ + '.' + self.__class__.__name__
        )

        self._fetch_assets = fetch_assets
        self._fetch_assetversions = fetch_assetversions
        self._session = session

        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.setSpacing(1)
        self.assets = []

    def reload(self):
        '''We have a context, fetch assets in the background'''
        self.clear()

        thread = BaseThread(
            name='get_assets_thread',
            target=self._query_assets_from_context_async,
            callback=self._store_assets_async,
            target_args=(),
        )
        thread.start()

    def _query_assets_from_context_async(self):
        '''Fetch assets through callback'''
        return self._fetch_assets()

    def _store_assets_async(self, assets):
        '''Store assets and emit signal to have assets added to list'''
        self.assets = assets
        # Add data placeholder for new asset input
        self.assetsQueryDone.emit()

    def refresh(self):
        '''Add fetched assets to list'''
        self.clear()
        for asset_entity in self.assets:
            widget = AssetListItem(
                asset_entity,
                self.session,
                fetch_assetversions=self._fetch_assetversions,
            )
            widget.versionChanged.connect(self._on_version_changed_callback)
            list_item = QtWidgets.QListWidgetItem(self)
            list_item.setSizeHint(
                QtCore.QSize(
                    widget.sizeHint().width(), widget.sizeHint().height() + 5
                )
            )
            self.addItem(list_item)
            self.setItemWidget(list_item, widget)
        self.assetsAdded.emit()

    def _on_version_changed_callback(self, assetversion_entity):
        self.versionChanged.emit(assetversion_entity)


class NewAssetNameInput(QtWidgets.QLineEdit):
    '''Widget holding new asset name input'''

    clicked = QtCore.Signal()

    def __init__(self):
        super(NewAssetNameInput, self).__init__()

    def mousePressEvent(self, event):
        '''Override mouse press to emit signal'''
        self.clicked.emit()


class NewAssetInput(QtWidgets.QFrame):
    '''Widget holding new asset input during publish'''

    clicked = QtCore.Signal()

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

        self.name = NewAssetNameInput()
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
        self.name.clicked.connect(self.input_clicked)

    def mousePressEvent(self, event):
        '''Override mouse press to emit signal'''
        self.input_clicked()

    def input_clicked(self):
        '''Callback on user button or name click'''
        self.clicked.emit()


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


class AssetSelector(QtWidgets.QWidget):
    '''Widget for choosing an existing asset and asset version, or input asset
    name for creating a new asset, depending on mode.'''

    MODE_SELECT_ASSET = 'select_asset'
    MODE_SELECT_ASSET_CREATE = 'select_asset_create'
    MODE_SELECT_ASSETVERSION = 'select_assetversion'

    VALID_ASSET_NAME = QtCore.QRegExp('[A-Za-z0-9_]+')

    assetChanged = QtCore.Signal(object, object, object)
    '''Signal emitted when asset is changed, with asset name, asset entity and 
    is_valid_name flag'''

    versionChanged = QtCore.Signal(object)
    '''Signal emitted when version is changed, with assetversion entity as
    argument (version select mode)'''

    updateWidget = QtCore.Signal(object)

    @property
    def mode(self):
        '''Return mode of operation'''
        return self._mode

    @property
    def session(self):
        '''Return session'''
        return self._session

    def __init__(
        self,
        mode,
        fetch_assets,
        session,
        fetch_assetversions=None,
        parent=None,
    ):
        '''
        Initialise asset selector widget.

        :param mode: The mode of operation.
        :param fetch_assets: Callback to fetch assets
        :param fetch_assetversions:
        :param parent:
        '''
        super(AssetSelector, self).__init__(parent=parent)
        self.logger = logging.getLogger(
            __name__ + '.' + self.__class__.__name__
        )

        self._mode = mode
        self._fetch_assets = fetch_assets
        self._session = session
        self._fetch_assetversions = fetch_assetversions

        self._label = None
        self._list_and_input = None
        self._asset_list = None
        self._new_asset_input = None

        self.validator = QtGui.QRegExpValidator(self.VALID_ASSET_NAME)
        self.placeholder_name = "Asset Name..."

        self.pre_build()
        self.build()
        self.post_build()

    def pre_build(self):
        main_layout = QtWidgets.QVBoxLayout()
        self.setLayout(main_layout)

    def build(self):
        self._label = QtWidgets.QLabel()
        self._label.setObjectName('gray')
        self._label.setWordWrap(True)
        self.layout().addWidget(self._label)

        self._list_and_input = AssetListAndInput()

        self._asset_list = AssetList(
            self._fetch_assets, self._fetch_assetversions, self.session
        )
        self._asset_list.setVisible(False)
        self._list_and_input.add_asset_list(self._asset_list)

        if self.mode == self.MODE_SELECT_ASSET_CREATE:
            # Create new asset
            self._new_asset_input = NewAssetInput(
                self.validator, self.placeholder_name
            )
            self._list_and_input.layout().addWidget(self._new_asset_input)

        self.layout().addWidget(self._list_and_input)

    def post_build(self):
        self._asset_list.itemChanged.connect(self._current_asset_changed)
        self._asset_list.assetsQueryDone.connect(self._refresh)
        self._asset_list.assetsAdded.connect(self._pre_select_asset)
        self._asset_list.itemActivated.connect(self._list_selection_updated)
        self._asset_list.itemSelectionChanged.connect(
            self._list_selection_updated
        )
        self._asset_list.versionChanged.connect(
            self._on_version_changed_callback
        )
        self._new_asset_input.clicked.connect(self._current_asset_changed)
        self._new_asset_input.name.textChanged.connect(self._new_asset_changed)
        self.updateWidget.connect(self._update_widget)

    def _refresh(self):
        '''Add assets queried in separate thread to list.'''
        self._asset_list.refresh()

    def _pre_select_asset(self):
        '''Assets have been loaded, select most suitable asset to start with'''
        if self._asset_list.count() > 0:
            self._label.setText(
                'We found {} assets already '
                'published on this task. Choose which one to version up or create '
                'a new asset'.format(self._asset_list.count())
            )

            self._asset_list.setCurrentRow(0)
            self._label.show()
            self._asset_list.show()
            self._current_asset_changed(self._asset_list.item(0))
        else:
            self._label.setText('Enter asset name')
            self._asset_list.hide()
            self._current_asset_changed()
        self._list_and_input.size_changed()

    def _list_selection_updated(self):
        '''React upon user list selection'''
        selected_index = self._asset_list.currentRow()
        if selected_index == -1:
            # Deselected, give focus to new asset input
            self.updateWidget.emit(None)
        else:
            self._current_asset_changed(
                self._asset_list.assets[selected_index]
            )

    def _current_asset_changed(self, item=None):
        '''An existing asset *item* has been selected, or None if current is de-selected.'''
        print('@@@ _current_asset_changed; item: {}'.format(item))
        asset_entity = None
        asset_widget = None
        if item is not None:
            selected_index = self._asset_list.currentRow()
            if selected_index > -1:
                # A proper asset were selected
                asset_entity = self._asset_list.assets[selected_index]
        if asset_entity:
            asset_name = asset_entity['name']
            is_valid_name = self.validate_name(asset_name)
            self.assetChanged.emit(asset_name, asset_entity, is_valid_name)
            # self.versionChanged.emit(..)
            self.updateWidget.emit(asset_entity)
        else:
            # All items de-selected
            self._new_asset_changed()
            self.versionChanged.emit(None)
            self.updateWidget.emit(None)

    def _update_widget(self, selected_asset=None):
        '''Synchronize state of list with new asset input if *selected_asset* is
        None, otherwise bring focus to list.'''
        self._asset_list.ensurePolished()
        if selected_asset is not None:
            # Bring focus to list, remove focus from new asset input
            set_property(self._new_asset_input, 'status', 'unfocused')
            self._new_asset_input.name.setEnabled(False)
            self._new_asset_input.name.deselect()
        else:
            # Deselect all assets in list, bring focus to new asset input
            self._asset_list.setCurrentRow(-1)
            set_property(self._new_asset_input, 'status', 'focused')
            self._new_asset_input.name.setEnabled(True)
        self._new_asset_input.button.setEnabled(True)

    def set_asset_name(self, asset_name):
        '''Update the asset input widget with *asset_name*'''
        assert asset_name, 'No asset name provided'
        self.logger.debug('setting asset name to: {}'.format(asset_name))
        self._new_asset_input.name.setText(asset_name)

    def _new_asset_changed(self):
        '''New asset name text changed'''
        asset_name = self._new_asset_input.name.text()
        is_valid_name = self.validate_name(asset_name)
        self.assetChanged.emit(asset_name, None, is_valid_name)

    def validate_name(self, asset_name):
        '''Return True if *asset_name* is valid, also reflect this on input style'''
        is_valid_bool = True
        # Already an asset by that name
        if self._asset_list.assets:
            for asset_entity in self._asset_list.assets:
                if asset_entity['name'].lower() == asset_name.lower():
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

    def reload(self):
        '''Reload the asset list and versions'''
        self._asset_list.reload()

    def _on_version_changed_callback(self, assetversion_entity):
        self.versionChanged.emit(assetversion_entity)
