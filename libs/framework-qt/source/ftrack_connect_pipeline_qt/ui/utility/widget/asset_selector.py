# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack
import datetime
import logging

from Qt import QtWidgets, QtCore, QtGui

from ftrack_connect_pipeline import utils as core_utils

from ftrack_connect_pipeline_qt.ui.utility.widget.button import NewAssetButton
from ftrack_connect_pipeline_qt.utils import BaseThread
from ftrack_connect_pipeline_qt.ui.utility.widget.thumbnail import AssetVersion
from ftrack_connect_pipeline_qt.utils import set_property


class AssetListItem(QtWidgets.QFrame):
    '''Widget representing an asset within the list, for user selection'''

    def __init__(self, asset, session):
        super(AssetListItem, self).__init__()

        self.asset = asset
        self.session = session
        self.pre_build()
        self.build()

    def pre_build(self):
        self.setLayout(QtWidgets.QHBoxLayout())
        self.layout().setContentsMargins(0, 0, 0, 0)
        self.layout().setSpacing(5)

    def build(self):
        self.thumbnail_widget = AssetVersion(self.session)
        self.thumbnail_widget.setScaledContents(True)
        self.thumbnail_widget.setMinimumSize(57, 31)
        self.thumbnail_widget.setMaximumSize(57, 31)
        self.layout().addWidget(self.thumbnail_widget)
        self.thumbnail_widget.load(self.asset['latest_version']['id'])

        self.asset_name = QtWidgets.QLabel(self.asset['name'])
        self.layout().addWidget(self.asset_name)

        self.create_label = QtWidgets.QLabel('- create')
        self.create_label.setObjectName("gray")
        self.layout().addWidget(self.create_label)

        self.version_label = QtWidgets.QLabel(
            'Version {}'.format(self.asset['latest_version']['version'] + 1)
        )
        self.version_label.setObjectName("color-primary")
        self.layout().addWidget(self.version_label)

        self.layout().addStretch()

        self.setToolTip(core_utils.str_context(self.asset['parent']))


class AssetList(QtWidgets.QListWidget):
    '''Widget presenting list of existing assets'''

    assetsQueryDone = QtCore.Signal()  # Assets have been queried from ftrack
    assetsAdded = QtCore.Signal()  # Assets have been added to the widget

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

    def on_context_changed(self, context_id, asset_type_name):
        '''We have a context, fetch assets in the background'''
        self.clear()

        thread = BaseThread(
            name='get_assets_thread',
            target=self._query_assets_from_context_async,
            callback=self._store_assets_async,
            target_args=(context_id, asset_type_name),
        )
        thread.start()

    def _query_assets_from_context_async(self, context_id, asset_type_name):
        '''Fetch assets from current context'''
        asset_type_entity = self.session.query(
            'select name from AssetType where short is "{}"'.format(
                asset_type_name
            )
        ).first()
        # Determine if we have a task or not
        context = self.session.get('Context', context_id)
        # If it's a fake asset, context will be None so return empty list.
        if not context:
            return []
        if context.entity_type == 'Task':
            assets = self.session.query(
                'select name, versions.task.id, type.id, id, latest_version,'
                'latest_version.version '
                'from Asset where versions.task.id is {} and type.id is {}'.format(
                    context_id, asset_type_entity['id']
                )
            ).all()
        else:
            assets = self.session.query(
                'select name, versions.task.id, type.id, id, latest_version,'
                'latest_version.version '
                'from Asset where parent.id is {} and type.id is {}'.format(
                    context_id, asset_type_entity['id']
                )
            ).all()
        return assets

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
        self.button = NewAssetButton()
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
        self.asset_list = asset_list
        self.layout().addWidget(asset_list)

    def resizeEvent(self, event):
        '''(Override)'''
        self._size_changed()

    def _size_changed(self):
        '''Resize asset list to fit widget, to prevent unnecessary scrolling'''
        self.asset_list.setFixedSize(
            self.size().width() - 1,
            self.asset_list.sizeHintForRow(0) * self.asset_list.count()
            + 2 * self.asset_list.frameWidth(),
        )


class AssetSelector(QtWidgets.QWidget):
    '''Widget for choosing an existing asset to publish on, or input asset name for creating a new asset'''

    VALID_ASSET_NAME = QtCore.QRegExp('[A-Za-z0-9_]+')

    assetChanged = QtCore.Signal(object, object, object)
    updateWidget = QtCore.Signal(object)

    def __init__(self, session, parent=None):
        super(AssetSelector, self).__init__(parent=parent)
        self.logger = logging.getLogger(
            __name__ + '.' + self.__class__.__name__
        )

        self.session = session

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

        self.list_and_input = AssetListAndInput()

        self.asset_list = AssetList(self.session)
        self.asset_list.setVisible(False)
        self.list_and_input.add_asset_list(self.asset_list)
        # Create new asset
        self.new_asset_input = NewAssetInput(
            self.validator, self.placeholder_name
        )
        self.list_and_input.layout().addWidget(self.new_asset_input)

        self.layout().addWidget(self.list_and_input)

    def post_build(self):
        self.asset_list.itemChanged.connect(self._current_asset_changed)
        self.asset_list.assetsQueryDone.connect(self._refresh)
        self.asset_list.assetsAdded.connect(self._pre_select_asset)
        self.asset_list.itemActivated.connect(self._list_selection_updated)
        self.asset_list.itemSelectionChanged.connect(
            self._list_selection_updated
        )
        self.new_asset_input.clicked.connect(self._current_asset_changed)
        self.new_asset_input.name.textChanged.connect(self._new_asset_changed)
        self.updateWidget.connect(self._update_widget)

    def _refresh(self):
        '''Add assets queried in separate thread to list.'''
        self.asset_list.refresh()

    def _pre_select_asset(self):
        '''Assets have been loaded, select most suitable asset to start with'''
        if self.asset_list.count() > 0:
            self._label.setText(
                'We found {} assets already '
                'published on this task. Choose which one to version up or create '
                'a new asset'.format(self.asset_list.count())
            )

            self.asset_list.setCurrentRow(0)
            self._label.show()
            self.asset_list.show()
            self._current_asset_changed(self.asset_list.item(0))
        else:
            self._label.setText('Enter asset name')
            self.asset_list.hide()
            self._current_asset_changed()
        self.list_and_input._size_changed()

    def _list_selection_updated(self):
        '''React upon user list selection'''
        selected_index = self.asset_list.currentRow()
        if selected_index == -1:
            # Deselected, give focus to new asset input
            self.updateWidget.emit(None)
        else:
            self._current_asset_changed(self.asset_list.assets[selected_index])

    def _current_asset_changed(self, item=None):
        '''An existing asset *item* has been selected, or None if current is de-selected.'''
        asset_entity = None
        if not item is None:
            selected_index = self.asset_list.currentRow()
            if selected_index > -1:
                # A proper asset were selected
                asset_entity = self.asset_list.assets[selected_index]
        if asset_entity:
            asset_name = asset_entity['name']
            is_valid_name = self.validate_name(asset_name)
            self.assetChanged.emit(asset_name, asset_entity, is_valid_name)
            self.updateWidget.emit(asset_entity)
        else:
            # All items de-selected
            self._new_asset_changed()
            self.updateWidget.emit(None)

    def _update_widget(self, selected_asset=None):
        '''Synchronize state of list with new asset input if *selected_asset* is None, otherwise bring focus to list.'''
        self.asset_list.ensurePolished()
        if selected_asset is not None:
            # Bring focus to list, remove focus from new asset input
            set_property(self.new_asset_input, 'status', 'unfocused')
            self.new_asset_input.name.setEnabled(False)
            self.new_asset_input.name.deselect()
        else:
            # Deselect all assets in list, bring focus to new asset input
            self.asset_list.setCurrentRow(-1)
            set_property(self.new_asset_input, 'status', 'focused')
            self.new_asset_input.name.setEnabled(True)
        self.new_asset_input.button.setEnabled(True)

    def set_context(self, context_id, asset_type_name):
        '''Set context to *context_id* and asset type to *asset_type_name*'''
        self.logger.debug('setting context to :{}'.format(context_id))
        self.asset_list.on_context_changed(context_id, asset_type_name)
        self.set_asset_name(asset_type_name)

    def set_asset_name(self, asset_name):
        '''Update the asset input widget with *asset_name*'''
        self.logger.debug('setting asset name to :{}'.format(asset_name))
        self.new_asset_input.name.setText(asset_name)

    def _new_asset_changed(self):
        '''New asset name text changed'''
        asset_name = self.new_asset_input.name.text()
        is_valid_name = self.validate_name(asset_name)
        self.assetChanged.emit(asset_name, None, is_valid_name)

    def validate_name(self, asset_name):
        '''Return True if *asset_name* is valid, also reflect this on input style'''
        is_valid_bool = True
        # Already an asset by that name
        if self.asset_list.assets:
            for asset_entity in self.asset_list.assets:
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
            set_property(self.new_asset_input.name, 'input', '')
        else:
            set_property(self.new_asset_input.name, 'input', 'invalid')
        return is_valid_bool
