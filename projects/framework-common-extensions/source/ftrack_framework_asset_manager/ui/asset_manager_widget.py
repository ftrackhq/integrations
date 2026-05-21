# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

"""Asset manager widgets for ftrack."""

import json
import platform
from functools import partial

try:
    from PySide6 import QtWidgets, QtCore, QtGui
except ImportError:
    from PySide2 import QtWidgets, QtCore, QtGui

try:
    from shiboken2 import isValid
except ImportError:

    def isValid(obj):
        """Fallback for shiboken2.isValid."""
        return True


from ftrack_framework_asset_manager.asset.constants import (
    ASSET_INFO_OPTIONS,
)
from ftrack_framework_asset_manager.asset.ftrack_asset_info import (
    FtrackAssetInfo,
)
from ftrack_framework_asset_manager.asset.asset_list_model import (
    AssetListModel,
)

try:
    from ftrack_qt.widgets.accordion import AccordionBaseWidget
except ImportError:
    from ftrack_qt.widgets.base import AccordionBaseWidget

from ftrack_qt.widgets.overlay import BusyIndicator

try:
    from ftrack_qt.widgets.search import Search
except ImportError:

    class Search(QtWidgets.QLineEdit):
        """Simple search widget fallback."""

        textChanged = QtCore.Signal(str)

        def __init__(self, parent=None):
            super(Search, self).__init__(parent)
            self.textChanged.connect(self._on_text_changed)
            self.setPlaceholderText("Search...")

        def _on_text_changed(self, text):
            self.textChanged.emit(text)


try:
    from ftrack_qt.widgets.thumb import AssetVersion as AssetVersionThumbnail
except ImportError:

    class AssetVersionThumbnail(QtWidgets.QLabel):
        """Simple thumbnail widget fallback."""

        pass


try:
    from ftrack_qt.widgets.entity import EntityInfo
except ImportError:

    class EntityInfo(QtWidgets.QLabel):
        """Simple entity info widget fallback."""

        pass


class AssetManagerBaseWidget(QtWidgets.QWidget):
    """Base widget for the asset manager."""

    def __init__(self, event_manager, asset_list_model, parent=None):
        """Initialize the base widget.

        Args:
            event_manager: The event manager instance.
            asset_list_model: The asset list model instance.
            parent: The parent widget.
        """
        super(AssetManagerBaseWidget, self).__init__(parent=parent)

        self._event_manager = event_manager
        self._asset_list_model = asset_list_model
        self._engine_type = None

        # Set up layout
        self._layout = QtWidgets.QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)

        self.pre_build()
        self.build()
        self.post_build()

    @property
    def event_manager(self):
        """Return the event manager."""
        return self._event_manager

    @property
    def session(self):
        """Return the session from the event manager."""
        return self._event_manager.session if self._event_manager else None

    @property
    def engine_type(self):
        """Return the engine type."""
        return self._engine_type

    @engine_type.setter
    def engine_type(self, value):
        """Set the engine type."""
        self._engine_type = value

    def pre_build(self):
        """Pre-build setup."""
        pass

    def build(self):
        """Build the widget."""
        pass

    def post_build(self):
        """Post-build setup."""
        pass

    def build_header(self, layout):
        """Build the header layout.

        Args:
            layout: The layout to add the header to.
        """
        pass

    def init_search(self):
        """Initialize the search functionality."""
        pass

    def on_search(self, text):
        """Handle search text changes.

        Args:
            text: The search text.
        """
        pass


class AssetManagerWidget(AssetManagerBaseWidget):
    """Main asset manager widget."""

    # Signals
    refresh = QtCore.Signal()
    rebuild = QtCore.Signal()
    changeAssetVersion = QtCore.Signal(object, object)
    selectAssets = QtCore.Signal(object, object)
    removeAssets = QtCore.Signal(object, object)
    updateAssets = QtCore.Signal(object, object)
    loadAssets = QtCore.Signal(object, object)
    unloadAssets = QtCore.Signal(object, object)
    stopBusyIndicator = QtCore.Signal()

    DEFAULT_ACTIONS = {
        'select': 'Select',
        'load': 'Load',
        'update': 'Update',
        'unload': 'Unload',
        'remove': 'Remove',
    }

    def __init__(self, event_manager, asset_list_model, parent=None):
        """Initialize the asset manager widget.

        Args:
            event_manager: The event manager instance.
            asset_list_model: The asset list model instance.
            parent: The parent widget.
        """
        super(AssetManagerWidget, self).__init__(
            event_manager, asset_list_model, parent=parent
        )

        self._busy_indicator = None
        self._search_widget = None
        self._asset_list_widget = None
        self._scroll_area = None

        self._actions = {}
        self._selected_assets = []

    def pre_build(self):
        """Pre-build setup."""
        # Layout already created by AssetManagerBaseWidget.__init__;
        # creating another QVBoxLayout(self) here would leave _layout
        # pointing to an orphaned layout, so children added in build()
        # would never render.

    def build_header(self, layout):
        """Build the header layout.

        Args:
            layout: The layout to add the header to.
        """
        header_layout = QtWidgets.QHBoxLayout()
        header_layout.setContentsMargins(6, 6, 6, 6)
        header_layout.setSpacing(6)

        # Title label
        title_label = QtWidgets.QLabel("Asset Manager")
        title_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        header_layout.addWidget(title_label)

        # Stretch to push buttons to the right
        header_layout.addStretch()

        # Rebuild button
        rebuild_button = QtWidgets.QPushButton("Rebuild")
        rebuild_button.setToolTip("Rebuild the asset list")
        rebuild_button.clicked.connect(self._on_rebuild)
        header_layout.addWidget(rebuild_button)

        # Busy indicator
        self._busy_indicator = BusyIndicator(start=False, parent=self)
        self._busy_indicator.setFixedSize(20, 20)
        self._busy_indicator.setVisible(False)
        header_layout.addWidget(self._busy_indicator)

        # Search widget
        self._search_widget = Search(self)
        self._search_widget.setPlaceholderText("Search assets...")
        self._search_widget.setFixedWidth(200)
        self._search_widget.textChanged.connect(self.on_search)
        header_layout.addWidget(self._search_widget)

        layout.addLayout(header_layout)

    def build(self):
        """Build the widget."""
        # Build header
        self.build_header(self._layout)

        # Scroll area for asset list
        self._scroll_area = QtWidgets.QScrollArea(self)
        self._scroll_area.setWidgetResizable(True)
        self._scroll_area.setFrameShape(QtWidgets.QFrame.NoFrame)
        self._scroll_area.setContentsMargins(0, 0, 0, 0)

        # Asset list widget
        self._asset_list_widget = AssetManagerListWidget(
            self._asset_list_model, AssetWidget, self
        )
        self._asset_list_widget.selectionUpdated.connect(
            self._on_selection_updated
        )
        self._asset_list_widget.changeAssetVersion.connect(
            self.changeAssetVersion
        )

        self._scroll_area.setWidget(self._asset_list_widget)
        self._layout.addWidget(self._scroll_area)

    def post_build(self):
        """Post-build setup."""
        # Connect signals
        self.refresh.connect(self._on_refresh)
        self.rebuild.connect(self._on_rebuild)
        self.changeAssetVersion.connect(self._on_change_asset_version)

    def set_asset_list(self, asset_entities_list):
        """Set the asset list.

        Args:
            asset_entities_list: List of asset entities.
        """
        self._asset_list_model.reset()
        if asset_entities_list:
            self._asset_list_model.insertRows(0, list(asset_entities_list))

    def set_busy(self, busy):
        """Show or hide the busy indicator.

        Args:
            busy: Whether to show the busy indicator.
        """
        if self._busy_indicator:
            self._busy_indicator.setVisible(busy)
            if busy:
                self._busy_indicator.start()
            else:
                self._busy_indicator.stop()

    def create_actions(self):
        """Create context menu actions."""
        self._actions = {}
        for action_id, action_text in self.DEFAULT_ACTIONS.items():
            action = QtWidgets.QAction(action_text, self)
            action.setData(action_id)
            self._actions[action_id] = action

    def contextMenuEvent(self, event):
        """Handle context menu events.

        Args:
            event: The context menu event.
        """
        if not self._actions:
            self.create_actions()

        menu = QtWidgets.QMenu(self)
        for action in self._actions.values():
            menu.addAction(action)

        # Show menu and connect triggered signal
        action = menu.exec_(event.globalPos())
        if action:
            self.menu_triggered(action)

    def menu_triggered(self, action):
        """Handle menu action triggered.

        Args:
            action: The triggered action.
        """
        action_id = action.data()
        if action_id == 'select':
            self.ctx_select()
        elif action_id == 'load':
            self.ctx_load()
        elif action_id == 'update':
            self.ctx_update()
        elif action_id == 'unload':
            self.ctx_unload()
        elif action_id == 'remove':
            self.ctx_remove()

    def ctx_select(self):
        """Handle select action."""
        selected_assets = self._asset_list_widget.selection()
        if selected_assets:
            self.selectAssets.emit(selected_assets, self._engine_type)

    def ctx_load(self):
        """Handle load action."""
        selected_assets = self._asset_list_widget.selection()
        if selected_assets:
            self.loadAssets.emit(selected_assets, self._engine_type)

    def ctx_update(self):
        """Handle update action."""
        selected_assets = self._asset_list_widget.selection()
        if selected_assets:
            self.updateAssets.emit(selected_assets, self._engine_type)

    def ctx_unload(self):
        """Handle unload action."""
        selected_assets = self._asset_list_widget.selection()
        if selected_assets:
            self.unloadAssets.emit(selected_assets, self._engine_type)

    def ctx_remove(self):
        """Handle remove action."""
        selected_assets = self._asset_list_widget.selection()
        if selected_assets:
            self.removeAssets.emit(selected_assets, self._engine_type)

    def check_selection(self):
        """Check if there is a valid selection.

        Returns:
            bool: Whether there is a valid selection.
        """
        return bool(self._asset_list_widget.selection())

    def _on_refresh(self):
        """Handle refresh signal."""
        self._asset_list_widget.refresh()

    def _on_rebuild(self):
        """Handle rebuild signal."""
        self._asset_list_widget.rebuild()

    def _on_change_asset_version(self, asset_info, version_id):
        """Handle change asset version signal.

        Args:
            asset_info: The asset info.
            version_id: The version ID.
        """
        self.changeAssetVersion.emit(asset_info, version_id)

    def _on_selection_updated(self, selected_assets):
        """Handle selection updated signal.

        Args:
            selected_assets: List of selected assets.
        """
        self._selected_assets = selected_assets


class AssetManagerListWidget(QtWidgets.QWidget):
    """Asset list container widget."""

    selectionUpdated = QtCore.Signal(object)
    refreshed = QtCore.Signal()
    changeAssetVersion = QtCore.Signal(object, object)

    def __init__(self, model, asset_widget_class, parent=None):
        """Initialize the asset list widget.

        Args:
            model: The asset list model.
            asset_widget_class: The asset widget class to use.
            parent: The parent widget.
        """
        super(AssetManagerListWidget, self).__init__(parent=parent)

        self._model = model
        self._asset_widget_class = asset_widget_class
        self._assets = []
        self._selected_assets = []

        # Set up layout
        self._layout = QtWidgets.QVBoxLayout(self)
        self._layout.setContentsMargins(6, 0, 6, 6)
        self._layout.setSpacing(6)
        self._layout.setAlignment(QtCore.Qt.AlignTop)

        # Connect model signals
        self._model.rowsInserted.connect(self.rebuild)
        self._model.modelReset.connect(self.rebuild)
        self._model.rowsRemoved.connect(self.rebuild)
        self._model.dataChanged.connect(self.rebuild)

        self.rebuild()

    @property
    def model(self):
        """Return the model."""
        return self._model

    @property
    def assets(self):
        """Return the asset widgets."""
        return self._assets

    def rebuild(self):
        """Rebuild the asset list."""
        # Clear existing assets
        for asset_widget in self._assets:
            if isValid(asset_widget):
                asset_widget.setParent(None)
                asset_widget.deleteLater()
        self._assets = []

        # Create new assets
        for row in range(self._model.rowCount()):
            index = self._model.index(row, 0)
            asset_info = self._model.data(index, QtCore.Qt.UserRole)

            asset_widget = self._asset_widget_class(index, self._model, self)
            asset_widget.set_asset_info(asset_info)
            asset_widget.changeAssetVersion.connect(self.changeAssetVersion)
            asset_widget.clicked.connect(
                partial(self.asset_clicked, asset_widget)
            )

            self._layout.addWidget(asset_widget)
            self._assets.append(asset_widget)

        # Add stretch to push assets to the top
        self._layout.addStretch()

        self.refreshed.emit()

    def refresh(self, search_text=None):
        """Refresh the asset list.

        Args:
            search_text: Optional search text to filter assets.
        """
        if search_text is None:
            search_text = (
                self._search_widget.text()
                if hasattr(self, '_search_widget')
                else ''
            )

        for asset_widget in self._assets:
            if isValid(asset_widget):
                if search_text:
                    asset_widget.setVisible(asset_widget.matches(search_text))
                else:
                    asset_widget.setVisible(True)

    def on_search(self, text):
        """Handle search text changes.

        Args:
            text: The search text.
        """
        self.refresh(text)

    def selection(self, as_widgets=False):
        """Return the selected assets.

        Args:
            as_widgets: Whether to return widgets or asset infos.

        Returns:
            List of selected assets.
        """
        if as_widgets:
            return self._selected_assets
        else:
            return [
                asset_widget.asset_info
                for asset_widget in self._selected_assets
            ]

    def clear_selection(self):
        """Clear the selection."""
        for asset_widget in self._selected_assets:
            if isValid(asset_widget):
                asset_widget.set_selected(False)
        self._selected_assets = []
        self.selectionUpdated.emit(self._selected_assets)

    def asset_clicked(self, clicked_widget):
        """Handle asset clicked.

        Args:
            clicked_widget: The clicked asset widget.
        """
        modifiers = QtWidgets.QApplication.keyboardModifiers()

        if modifiers & QtCore.Qt.ControlModifier:
            # Ctrl+Click: Toggle selection
            if clicked_widget in self._selected_assets:
                self._selected_assets.remove(clicked_widget)
                clicked_widget.set_selected(False)
            else:
                self._selected_assets.append(clicked_widget)
                clicked_widget.set_selected(True)
        elif modifiers & QtCore.Qt.ShiftModifier:
            # Shift+Click: Range selection
            if not self._selected_assets:
                # No existing selection, select only clicked
                self._selected_assets = [clicked_widget]
                clicked_widget.set_selected(True)
            else:
                # Find range between last selected and clicked
                last_selected = self._selected_assets[-1]
                last_index = self._assets.index(last_selected)
                clicked_index = self._assets.index(clicked_widget)

                start = min(last_index, clicked_index)
                end = max(last_index, clicked_index)

                # Clear current selection
                for asset_widget in self._selected_assets:
                    if isValid(asset_widget):
                        asset_widget.set_selected(False)

                # Select range
                self._selected_assets = []
                for i in range(start, end + 1):
                    asset_widget = self._assets[i]
                    if isValid(asset_widget):
                        asset_widget.set_selected(True)
                        self._selected_assets.append(asset_widget)
        else:
            # Regular click: Select only clicked
            self.clear_selection()
            self._selected_assets = [clicked_widget]
            clicked_widget.set_selected(True)

        self.selectionUpdated.emit(self.selection())


class AssetWidget(AccordionBaseWidget):
    """Individual asset display widget."""

    changeAssetVersion = QtCore.Signal(object, object)

    def __init__(self, index, model, parent=None):
        """Initialize the asset widget.

        Args:
            index: The model index.
            model: The asset list model.
            parent: The parent widget.
        """
        super(AssetWidget, self).__init__(parent=parent)

        self._index = index
        self._model = model
        self._asset_info = None
        self._selected = False

        self.setStyleSheet(
            """
            AssetWidget {
                border: 1px solid #333;
                border-radius: 4px;
                padding: 8px;
                margin-bottom: 4px;
            }
            AssetWidget[selected="true"] {
                background-color: #444;
            }
        """
        )

    def init_header_content(self):
        """Initialize the header content."""
        header_layout = QtWidgets.QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(6)

        # Path label
        self._path_label = QtWidgets.QLabel()
        self._path_label.setStyleSheet("color: #999;")
        header_layout.addWidget(self._path_label)

        # Asset name label
        self._asset_name_label = QtWidgets.QLabel()
        self._asset_name_label.setStyleSheet("font-weight: bold;")
        header_layout.addWidget(self._asset_name_label)

        # Component and version widget
        self._component_version_widget = ComponentAndVersionWidget(self)
        header_layout.addWidget(self._component_version_widget)

        # Status widget
        self._status_widget = AssetVersionStatusWidget(self)
        header_layout.addWidget(self._status_widget)

        # Stretch to push status to the right
        header_layout.addStretch()

        self.set_header_layout(header_layout)

    def set_asset_info(self, asset_info):
        """Set the asset info.

        Args:
            asset_info: The asset info dictionary.
        """
        self._asset_info = asset_info

        if not asset_info:
            return

        # Set header content
        self._path_label.setText(asset_info.get('path', ''))
        self._asset_name_label.setText(asset_info.get('asset_name', ''))

        # Set component and version
        component_path = asset_info.get('component_path', '')
        version_nr = asset_info.get('version_nr', 0)
        versions = asset_info.get('versions', [])

        self._component_version_widget.set_component_filename(component_path)
        self._component_version_widget.set_version(version_nr, versions)

        # Set status
        status = asset_info.get('status', 'unknown')
        self._status_widget.set_status(status)

    def matches(self, search_text):
        """Check if the asset matches the search text.

        Args:
            search_text: The search text.

        Returns:
            bool: Whether the asset matches the search text.
        """
        if not search_text:
            return True

        if not self._asset_info:
            return False

        search_lower = search_text.lower()

        # Check all relevant fields
        fields_to_check = [
            self._asset_info.get('path', ''),
            self._asset_info.get('asset_name', ''),
            self._asset_info.get('component_path', ''),
            self._asset_info.get('status', ''),
        ]

        for field in fields_to_check:
            if search_lower in field.lower():
                return True

        return False

    def on_collapse(self, collapsed):
        """Handle collapse state changes.

        Args:
            collapsed: Whether the widget is collapsed.
        """
        if collapsed:
            # Clear expanded content
            self.clear_content()
        else:
            # Populate expanded content
            if self._asset_info:
                self._populate_expanded_content()

    def _populate_expanded_content(self):
        """Populate the expanded content."""
        content_layout = QtWidgets.QVBoxLayout()
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(6)

        # Thumbnail
        thumbnail_widget = AssetVersionThumbnail(self)
        thumbnail_widget.setFixedSize(128, 128)
        content_layout.addWidget(thumbnail_widget)

        # Entity info
        entity_info = EntityInfo(self)
        entity_info.setText(
            "Entity: {}".format(self._asset_info.get('entity_type', 'Unknown'))
        )
        content_layout.addWidget(entity_info)

        # Dependencies
        dependencies_label = QtWidgets.QLabel("Dependencies:")
        dependencies_label.setStyleSheet("font-weight: bold;")
        content_layout.addWidget(dependencies_label)

        dependencies_text = QtWidgets.QTextEdit()
        dependencies_text.setReadOnly(True)
        dependencies_text.setPlainText(
            json.dumps(self._asset_info.get('dependencies', {}), indent=2)
        )
        content_layout.addWidget(dependencies_text)

        self.set_content_layout(content_layout)

    def set_selected(self, selected):
        """Set the selected state.

        Args:
            selected: Whether the widget is selected.
        """
        self._selected = selected
        self.setProperty('selected', selected)
        self.style().unpolish(self)
        self.style().polish(self)

    def is_selected(self):
        """Return whether the widget is selected.

        Returns:
            bool: Whether the widget is selected.
        """
        return self._selected

    @property
    def asset_info(self):
        """Return the asset info."""
        return self._asset_info


class AssetVersionStatusWidget(QtWidgets.QFrame):
    """Asset version status badge widget."""

    def __init__(self, parent=None):
        """Initialize the status widget.

        Args:
            parent: The parent widget.
        """
        super(AssetVersionStatusWidget, self).__init__(parent=parent)

        self._status_label = QtWidgets.QLabel(self)
        self._status_label.setAlignment(QtCore.Qt.AlignCenter)

        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.addWidget(self._status_label)

        self.setStyleSheet(
            """
            AssetVersionStatusWidget {
                border-radius: 8px;
                padding: 2px 8px;
            }
        """
        )

    def set_status(self, status):
        """Set the status.

        Args:
            status: The status to display.
        """
        self._status_label.setText(status)

        # Set color based on status
        if status == 'loaded':
            self.setStyleSheet(
                """
                AssetVersionStatusWidget {
                    background-color: #4CAF50;
                    color: white;
                    border-radius: 8px;
                    padding: 2px 8px;
                }
            """
            )
        elif status == 'updated':
            self.setStyleSheet(
                """
                AssetVersionStatusWidget {
                    background-color: #2196F3;
                    color: white;
                    border-radius: 8px;
                    padding: 2px 8px;
                }
            """
            )
        elif status == 'unloaded':
            self.setStyleSheet(
                """
                AssetVersionStatusWidget {
                    background-color: #9E9E9E;
                    color: white;
                    border-radius: 8px;
                    padding: 2px 8px;
                }
            """
            )
        else:
            self.setStyleSheet(
                """
                AssetVersionStatusWidget {
                    background-color: #FF9800;
                    color: white;
                    border-radius: 8px;
                    padding: 2px 8px;
                }
            """
            )


class AssetVersionSelector(QtWidgets.QComboBox):
    """Asset version selector widget."""

    def __init__(self, parent=None):
        """Initialize the version selector.

        Args:
            parent: The parent widget.
        """
        super(AssetVersionSelector, self).__init__(parent=parent)

        self.setFixedWidth(100)
        self.setStyleSheet(
            """
            AssetVersionSelector {
                padding: 2px 8px;
                border: 1px solid #555;
                border-radius: 4px;
                background-color: #333;
                color: white;
            }
        """
        )


class ComponentAndVersionWidget(QtWidgets.QWidget):
    """Component filename and version widget."""

    def __init__(self, parent=None):
        """Initialize the component and version widget.

        Args:
            parent: The parent widget.
        """
        super(ComponentAndVersionWidget, self).__init__(parent=parent)

        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        # Component filename label
        self._component_label = QtWidgets.QLabel(self)
        self._component_label.setStyleSheet("color: #CCC;")
        layout.addWidget(self._component_label)

        # Version selector
        self._version_selector = AssetVersionSelector(self)
        self._version_selector.currentIndexChanged.connect(
            self._on_version_changed
        )
        layout.addWidget(self._version_selector)

    def set_latest_version(self, is_latest_version):
        """Set the latest version indicator.

        Args:
            is_latest_version: Whether this is the latest version.
        """
        if is_latest_version:
            self._component_label.setStyleSheet("color: #8BC34A;")
        else:
            self._component_label.setStyleSheet("color: #CCC;")

    def set_component_filename(self, component_path):
        """Set the component filename.

        Args:
            component_path: The component path.
        """
        # Extract just the filename
        filename = component_path.split('/')[-1] if component_path else ''
        self._component_label.setText(filename)

    def set_version(self, version_nr, versions=None):
        """Set the version.

        Args:
            version_nr: The version number.
            versions: Optional list of available versions.
        """
        if versions:
            # Populate selector with versions
            self._version_selector.clear()
            for version in versions:
                self._version_selector.addItem(str(version), version)

            # Set current version
            current_index = self._version_selector.findData(version_nr)
            if current_index >= 0:
                self._version_selector.setCurrentIndex(current_index)
        else:
            # Just display the version number
            self._version_selector.clear()
            self._version_selector.addItem(str(version_nr), version_nr)

    def _on_version_changed(self, index):
        """Handle version changed.

        Args:
            index: The new index.
        """
        version_id = self._version_selector.itemData(index)
        # Emit signal through parent widget if it has changeAssetVersion
        parent = self.parent()
        if hasattr(parent, 'changeAssetVersion'):
            parent.changeAssetVersion.emit(parent.asset_info, version_id)
