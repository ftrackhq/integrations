# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

"""Asset manager widgets for ftrack."""

import json
from functools import partial

try:
    from PySide6 import QtWidgets, QtCore, QtGui
except ImportError:
    from PySide2 import QtWidgets, QtCore, QtGui

try:
    from shiboken6 import isValid
except ImportError:
    try:
        from shiboken2 import isValid
    except ImportError:

        def isValid(obj):
            return obj is not None


import ftrack_constants as constants

from ftrack_qt.widgets.accordion import AccordionBaseWidget
from ftrack_qt.widgets.overlay import BusyIndicator
from ftrack_qt.widgets.icons import MaterialIcon
from ftrack_qt.widgets.lines import LineWidget
from ftrack_qt.widgets.selectors.version_selector import VersionSelector
from ftrack_qt.widgets.thumbnails import AssetVersionThumbnail


# Qt6 moved ``QAction`` from QtWidgets to QtGui. Use whichever module
# exposes it so the same code works under PySide2 and PySide6.
QAction = getattr(QtWidgets, "QAction", None) or QtGui.QAction


try:
    from ftrack_qt.widgets.search import Search
except ImportError:

    class Search(QtWidgets.QLineEdit):
        """Plain-QLineEdit fallback used when ftrack_qt.widgets.search.Search
        is not packaged in this build."""

        def __init__(self, parent=None):
            super(Search, self).__init__(parent)
            self.setPlaceholderText("Search...")


class AssetManagerBaseWidget(QtWidgets.QWidget):
    """Base widget for the asset manager."""

    def __init__(self, event_manager, asset_list_model, parent=None):
        super(AssetManagerBaseWidget, self).__init__(parent=parent)

        self._event_manager = event_manager
        self._asset_list_model = asset_list_model
        self._engine_type = None

        self._layout = QtWidgets.QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)

        self.pre_build()
        self.build()
        self.post_build()

    @property
    def event_manager(self):
        return self._event_manager

    @property
    def session(self):
        return self._event_manager.session if self._event_manager else None

    @property
    def engine_type(self):
        return self._engine_type

    @engine_type.setter
    def engine_type(self, value):
        self._engine_type = value

    def pre_build(self):
        pass

    def build(self):
        pass

    def post_build(self):
        pass

    def on_search(self, text):
        pass


class AssetManagerWidget(AssetManagerBaseWidget):
    """Main asset manager widget."""

    changeAssetVersion = QtCore.Signal(object, object)
    selectAssets = QtCore.Signal(object, object)
    removeAssets = QtCore.Signal(object, object)
    updateAssets = QtCore.Signal(object, object)
    loadAssets = QtCore.Signal(object, object)
    unloadAssets = QtCore.Signal(object, object)
    selectInScene = QtCore.Signal(object)
    pendingChanged = QtCore.Signal(int)
    stopBusyIndicator = QtCore.Signal()

    DEFAULT_ACTIONS = {
        "select": "Select",
        "load": "Load",
        "update": "Update",
        "unload": "Unload",
        "remove": "Remove",
    }

    def __init__(self, event_manager, asset_list_model, parent=None):
        self._busy_indicator = None
        self._search_widget = None
        self._asset_list_widget = None

        super(AssetManagerWidget, self).__init__(
            event_manager, asset_list_model, parent=parent
        )

        self._actions = {}
        self._selected_assets = []

    def build_header(self, layout):
        header_layout = QtWidgets.QHBoxLayout()
        header_layout.setContentsMargins(6, 6, 6, 6)
        header_layout.setSpacing(6)

        title_label = QtWidgets.QLabel("Assets")
        title_label.setProperty("h2", True)
        header_layout.addWidget(title_label)

        header_layout.addStretch()

        self._busy_indicator = BusyIndicator(start=False, parent=self)
        self._busy_indicator.setFixedSize(20, 20)
        self._busy_indicator.setVisible(False)
        header_layout.addWidget(self._busy_indicator)

        self._search_widget = Search(self)
        self._search_widget.setPlaceholderText("Search assets...")
        self._search_widget.setFixedWidth(200)
        self._search_widget.textChanged.connect(self.on_search)
        header_layout.addWidget(self._search_widget)

        layout.addLayout(header_layout)

    def build(self):
        self.build_header(self._layout)

        # ``QListWidget`` scrolls itself — no outer ``QScrollArea`` needed.
        self._asset_list_widget = AssetManagerListWidget(
            self._asset_list_model, AssetWidget, self
        )
        self._asset_list_widget.selectionUpdated.connect(
            self._on_selection_updated
        )
        self._asset_list_widget.changeAssetVersion.connect(
            self.changeAssetVersion
        )
        self._asset_list_widget.selectInScene.connect(self.selectInScene)
        self._asset_list_widget.pendingChanged.connect(self.pendingChanged)
        self._asset_list_widget.contextMenuRequested.connect(
            self.show_context_menu
        )

        self._layout.addWidget(self._asset_list_widget)

    def set_asset_list(self, asset_entities_list):
        self._asset_list_model.reset()
        if asset_entities_list:
            self._asset_list_model.insertRows(0, list(asset_entities_list))

    def set_busy(self, busy):
        if self._busy_indicator:
            self._busy_indicator.setVisible(busy)
            if busy:
                self._busy_indicator.start()
            else:
                self._busy_indicator.stop()

    def on_search(self, text):
        if self._asset_list_widget:
            self._asset_list_widget.on_search(text)

    def pending_changes(self):
        """List of ``(asset_info, pending_version_dict)`` for staged rows."""
        if not self._asset_list_widget:
            return []
        return self._asset_list_widget.pending_changes()

    def clear_pending_changes(self):
        if self._asset_list_widget:
            self._asset_list_widget.clear_pending_changes()

    def create_actions(self):
        self._actions = {}
        for action_id, action_text in self.DEFAULT_ACTIONS.items():
            action = QAction(action_text, self)
            action.setData(action_id)
            self._actions[action_id] = action

    def show_context_menu(self, global_pos):
        """Build and show the context menu at ``global_pos``. Connected to
        ``AssetManagerListWidget.contextMenuRequested``, which fires from
        the list's ``contextMenuEvent`` override."""
        if not self._actions:
            self.create_actions()
        menu = QtWidgets.QMenu(self)
        for action in self._actions.values():
            menu.addAction(action)
        action = menu.exec_(global_pos)
        if action:
            self.menu_triggered(action)

    def menu_triggered(self, action):
        action_id = action.data()
        if action_id == "select":
            self.ctx_select()
        elif action_id == "load":
            self.ctx_load()
        elif action_id == "update":
            self.ctx_update()
        elif action_id == "unload":
            self.ctx_unload()
        elif action_id == "remove":
            self.ctx_remove()

    def ctx_select(self):
        # Selection-in-scene is the only context-menu action that runs
        # immediately; everything else is staged and applied via
        # APPLY CHANGES so the user gets a single review/commit step.
        sel = self._asset_list_widget.context_target()
        if sel:
            self.selectAssets.emit(sel, self._engine_type)

    def ctx_load(self):
        for widget in self._asset_list_widget.context_target_widgets():
            if (
                widget.asset_info
                and widget.asset_info.get("objects_loaded") is False
            ):
                widget.stage_action("load")

    def ctx_update(self):
        # Equivalent to picking the latest version in each row's dropdown.
        for widget in self._asset_list_widget.context_target_widgets():
            widget.stage_update_to_latest()

    def ctx_unload(self):
        for widget in self._asset_list_widget.context_target_widgets():
            if (
                widget.asset_info
                and widget.asset_info.get("objects_loaded") is not False
            ):
                widget.stage_action("unload")

    def ctx_remove(self):
        for widget in self._asset_list_widget.context_target_widgets():
            widget.stage_action("remove")

    def check_selection(self):
        return bool(self._asset_list_widget.selection())

    def _on_selection_updated(self, selected_assets):
        self._selected_assets = selected_assets


class _NoOpItemDelegate(QtWidgets.QStyledItemDelegate):
    """Item delegate that paints nothing. ``AssetManagerListWidget``
    uses ``setItemWidget`` to attach an ``AssetWidget`` for each row,
    and the AssetWidget handles all of its own rendering. The default
    delegate would still draw a selection background behind it — fine
    while the list has focus (covered by the SCSS ``::item:selected``
    rule), but in the inactive state the band bleeds through the row's
    transparent background as a thick yellow halo. Bypassing item
    painting entirely is simpler than wrestling with stylesheet
    pseudo-states and palette color groups."""

    def paint(self, painter, option, index):
        return

    def sizeHint(self, option, index):
        # Defer to the item's own size hint set by
        # ``AssetManagerListWidget.rebuild`` from ``AssetWidget.sizeHint``.
        return index.data(QtCore.Qt.SizeHintRole) or option.rect.size()


class AssetManagerListWidget(QtWidgets.QListWidget):
    """Asset list: one ``AssetWidget`` per scene asset, hung off a
    ``QListWidget`` via ``setItemWidget``. Selection (single, Ctrl, Shift)
    and right-click context menu are handled by ``QListWidget`` natively;
    each ``AssetWidget`` is a passive display widget whose ``selected``
    property is synced from the item's selection state in
    ``_on_item_selection_changed``."""

    selectionUpdated = QtCore.Signal(object)
    refreshed = QtCore.Signal()
    changeAssetVersion = QtCore.Signal(object, object)
    selectInScene = QtCore.Signal(object)
    pendingChanged = QtCore.Signal(int)
    contextMenuRequested = QtCore.Signal(object)
    """Emitted with the global ``QPoint`` when the user right-clicks a
    row. The outer ``AssetManagerWidget`` handles menu construction."""

    def __init__(self, model, asset_widget_class, parent=None):
        super(AssetManagerListWidget, self).__init__(parent=parent)

        self._model = model
        self._asset_widget_class = asset_widget_class
        self._assets = []
        self._search_text = ""
        # Populated by ``_on_context_menu_requested`` with the widgets
        # the next action should apply to — the persistent selection's
        # widgets, or just the right-clicked widget when the click landed
        # outside the selection.
        self._context_target_widgets = None
        # Re-entry guard: both ``mousePressEvent`` and ``contextMenuEvent``
        # can fire for the same right-click (platform-dependent). The
        # menu blocks on exec_(), so without this we'd open a second
        # menu when the second event is delivered during the first.
        self._menu_in_flight = False

        self.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.setSpacing(2)
        # Smooth pixel-based scrolling. The default is per-item, which
        # causes a visible jump when rows have very different heights
        # (e.g. an expanded accordion row next to collapsed ones).
        self.setVerticalScrollMode(QtWidgets.QAbstractItemView.ScrollPerPixel)
        self.setHorizontalScrollMode(
            QtWidgets.QAbstractItemView.ScrollPerPixel
        )

        self.itemSelectionChanged.connect(self._on_item_selection_changed)

        # The actual row visuals are drawn by the ``AssetWidget`` attached
        # via ``setItemWidget``. Qt's default item delegate would also
        # paint a selection background behind that widget — invisible
        # while the AssetWidget is on top, except in the inactive state
        # (focus elsewhere) where the band bleeds through the row's
        # transparent background as a thick yellow halo. Replacing the
        # delegate with a no-op stops *all* item painting; SCSS already
        # covers everything we actually want drawn.
        self.setItemDelegate(_NoOpItemDelegate(self))

        # Model -> view auto-rebuild on any data mutation.
        self._model.rowsInserted.connect(self.rebuild)
        self._model.modelReset.connect(self.rebuild)
        self._model.rowsRemoved.connect(self.rebuild)
        self._model.dataChanged.connect(self.rebuild)

        self.rebuild()

    @property
    def model(self):
        return self._model

    @property
    def assets(self):
        return self._assets

    def rebuild(self):
        # ``QListWidget.clear()`` removes items and the widgets attached
        # via setItemWidget.
        self.clear()
        self._assets = []
        self._context_target_widgets = None

        for row in range(self._model.rowCount()):
            index = self._model.index(row, 0)
            # AssetListModel.data() only returns the asset_info dict for
            # DisplayRole; UserRole returns None.
            asset_info = self._model.data(index, QtCore.Qt.DisplayRole)

            asset_widget = self._asset_widget_class(index, self._model, self)
            asset_widget.set_asset_info(asset_info)
            asset_widget.changeAssetVersion.connect(self.changeAssetVersion)
            asset_widget.selectInScene.connect(self.selectInScene)
            asset_widget.pendingChanged.connect(self._on_row_pending_changed)

            list_item = QtWidgets.QListWidgetItem(self)
            list_item.setSizeHint(asset_widget.sizeHint())
            self.setItemWidget(list_item, asset_widget)

            # When the accordion expands/collapses, refresh the item size
            # hint so the row grows/shrinks to fit. Defer to the next
            # event-loop tick because ``_on_collapse`` fires before
            # ``AccordionBaseWidget`` toggles the content widget's
            # visibility — sizeHint isn't accurate until after that.
            asset_widget.sizeHintChanged.connect(
                partial(
                    self._on_row_size_hint_changed, list_item, asset_widget
                )
            )

            self._assets.append(asset_widget)

            if self._search_text:
                list_item.setHidden(
                    not asset_widget.matches(self._search_text)
                )

        self.refreshed.emit()
        self.pendingChanged.emit(self._count_pending())

    def _count_pending(self):
        return sum(
            1 for w in self._assets if isValid(w) and w.has_pending_change()
        )

    def _on_row_pending_changed(self, _is_pending):
        self.pendingChanged.emit(self._count_pending())

    def _on_row_size_hint_changed(self, list_item, asset_widget):
        QtCore.QTimer.singleShot(
            0,
            partial(self._apply_row_size_hint, list_item, asset_widget),
        )

    def _apply_row_size_hint(self, list_item, asset_widget):
        if list_item is None or not isValid(asset_widget):
            return
        list_item.setSizeHint(asset_widget.sizeHint())

    def contextMenuEvent(self, event):
        """Canonical Qt entry point for right-clicks on the list.
        Propagates up from the deepest header child through the row
        widget to the QListWidget. ``QContextMenuEvent.globalPos()`` is
        the cross-platform-safe coordinate accessor here."""
        viewport_pos = self.viewport().mapFromGlobal(event.globalPos())
        self._on_context_menu_requested(viewport_pos)
        event.accept()

    def pending_changes(self):
        """Returns ``[(asset_info, action, data), ...]`` for every row
        that has a staged change. ``action`` is one of ``"version"``,
        ``"load"``, ``"unload"``, ``"remove"``. ``data`` is the
        new-version dict for ``"version"``, else ``None``."""
        result = []
        for w in self._assets:
            if not isValid(w) or not w.has_pending_change():
                continue
            action = w.pending_action
            data = w.pending_version if action == "version" else None
            result.append((w.asset_info, action, data))
        return result

    def clear_pending_changes(self):
        for w in self._assets:
            if isValid(w):
                w.clear_pending_change()

    def on_search(self, text):
        self._search_text = text or ""
        for i in range(self.count()):
            item = self.item(i)
            widget = self.itemWidget(item)
            if widget is None or not isValid(widget):
                continue
            if self._search_text:
                item.setHidden(not widget.matches(self._search_text))
            else:
                item.setHidden(False)

    def _on_item_selection_changed(self):
        """Push QListWidget's canonical selection state onto each
        AssetWidget's ``selected`` property so the SCSS rule
        ``AssetWidget[selected='true']`` drives the row visual."""
        for i in range(self.count()):
            item = self.item(i)
            widget = self.itemWidget(item)
            if widget is not None and isValid(widget):
                widget.set_selected(item.isSelected())
        self.selectionUpdated.emit(self.selection())

    def selection(self):
        return [
            self.itemWidget(item).asset_info
            for item in self.selectedItems()
            if self.itemWidget(item) is not None
        ]

    def selection_widgets(self):
        return [
            self.itemWidget(item)
            for item in self.selectedItems()
            if self.itemWidget(item) is not None
        ]

    def context_target(self):
        """Asset infos the next context-menu action should apply to.

        Returns the transient right-clicked row when the click landed
        outside the persistent selection (populated by
        ``_on_context_menu_requested``), otherwise the persistent
        selection itself."""
        widgets = self.context_target_widgets()
        return [w.asset_info for w in widgets if isValid(w)]

    def context_target_widgets(self):
        """Same selection contract as ``context_target`` but returns the
        ``AssetWidget`` instances. Callers that stage actions on rows
        (load/unload/remove/update) need widgets, not asset_info dicts."""
        if self._context_target_widgets is not None:
            return [w for w in self._context_target_widgets if isValid(w)]
        return self.selection_widgets()

    def _on_context_menu_requested(self, pos):
        """Right-click on the list. If the right-clicked row is in the
        persistent selection, target the full selection. Otherwise target
        just that row without disturbing the selection, and visually
        highlight it for the menu's duration. Empty-area right-clicks
        still open the menu, acting on the persistent selection."""
        if self._menu_in_flight:
            return

        item = self.itemAt(pos)
        widget = self.itemWidget(item) if item is not None else None

        transient_widget = None
        if widget is not None and isValid(widget):
            if item.isSelected():
                self._context_target_widgets = self.selection_widgets()
            else:
                self._context_target_widgets = [widget]
                widget.set_selected(True)
                transient_widget = widget
        else:
            # Empty-area click — act on the persistent selection.
            self._context_target_widgets = None

        self._menu_in_flight = True
        try:
            global_pos = self.viewport().mapToGlobal(pos)
            self.contextMenuRequested.emit(global_pos)
        finally:
            if transient_widget is not None and isValid(transient_widget):
                transient_widget.set_selected(False)
            self._context_target_widgets = None
            self._menu_in_flight = False


def _format_user_and_date(asset_info):
    first = asset_info.get("user_first_name") or ""
    last = asset_info.get("user_last_name") or ""
    date = asset_info.get("date") or ""
    user = "{} {}".format(first, last).strip()
    if user and date:
        return "{} @ {}".format(user, date)
    return user or date or ""


class AssetWidget(AccordionBaseWidget):
    """Single asset row: thumbnail, name, version dropdown, user @ date,
    component.file_type, select-in-scene button, status icon and expand arrow.
    """

    changeAssetVersion = QtCore.Signal(object, object)
    selectInScene = QtCore.Signal(object)
    pendingChanged = QtCore.Signal(bool)
    sizeHintChanged = QtCore.Signal()
    """Emitted when the row's expand state toggles, so the enclosing
    ``QListWidget`` can refresh its item size hint."""

    def __init__(self, index, model, parent=None):
        self._index = index
        self._model = model
        self._asset_info = None
        self._is_selected = False
        self._original_version_id = None
        self._pending_version = None
        self._pending_action = None  # "load" | "unload" | "remove" | None
        self._handling_dropdown_signal = False

        self._thumbnail_widget = None
        self._asset_name_label = None
        self._version_selector = None
        self._user_date_label = None
        self._component_label = None
        self._select_button = None

        self._content_built = False
        self._content_container = None

        super(AssetWidget, self).__init__(
            selectable=True,
            show_checkbox=False,
            checkable=False,
            collapsable=True,
            collapsed=True,
            parent=parent,
        )

    # -- AccordionBaseWidget lifecycle -----------------------------------

    def post_build(self):
        super(AssetWidget, self).post_build()
        # Hide the built-in gear (OptionsButton). The accordion always
        # constructs one inside AccordionHeaderWidget; the AM uses the
        # expanded panel for advanced metadata instead.
        if (
            self._header_widget is not None
            and self._header_widget._options_button is not None
        ):
            self._header_widget._options_button.hide()
        self._init_header_content()

    def _init_header_content(self):
        header_content = self._header_widget._header_content_widget
        layout = header_content.layout()

        # Wipe the default placeholder (status_label + stretch + LineWidget).
        while layout.count():
            item = layout.takeAt(0)
            w = item.widget()
            if w is not None:
                w.setParent(None)
                w.deleteLater()

        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        self._thumbnail_widget = AssetVersionThumbnail()
        self._thumbnail_widget.setScaledContents(True)
        self._thumbnail_widget.setMinimumSize(57, 31)
        self._thumbnail_widget.setMaximumSize(57, 31)
        layout.addWidget(self._thumbnail_widget)

        self._asset_name_label = QtWidgets.QLabel()
        self._asset_name_label.setProperty("asset_name", True)
        layout.addWidget(self._asset_name_label)

        self._version_selector = VersionSelector()
        self._version_selector.setMaximumHeight(20)
        layout.addWidget(self._version_selector)

        self._user_date_label = QtWidgets.QLabel()
        self._user_date_label.setProperty("secondary", True)
        layout.addWidget(self._user_date_label)

        self._component_label = QtWidgets.QLabel()
        self._component_label.setProperty("asset_path", True)
        layout.addWidget(self._component_label)

        layout.addStretch()

        self._select_button = QtWidgets.QToolButton()
        self._select_button.setIcon(MaterialIcon("my_location", color="gray"))
        self._select_button.setFixedSize(24, 24)
        self._select_button.setAutoRaise(True)
        self._select_button.setCheckable(False)
        self._select_button.setFocusPolicy(QtCore.Qt.NoFocus)
        self._select_button.setProperty("borderless", True)
        self._select_button.setToolTip("Select asset in scene")
        self._select_button.clicked.connect(self._on_select_in_scene_clicked)
        layout.addWidget(self._select_button)

        self._version_selector.currentIndexChanged.connect(
            self._on_version_selector_changed
        )

    def _on_collapse(self, collapsed):
        if not collapsed and self._asset_info and not self._content_built:
            self._populate_expanded_content()
            self._content_built = True
        # ``AccordionBaseWidget.toggle_collapsed`` calls this *before*
        # toggling the content widget's visibility, so the new
        # ``sizeHint()`` won't be valid until the next event-loop tick.
        # The list widget updates the item size hint then.
        self.sizeHintChanged.emit()

    # -- data binding ----------------------------------------------------

    def set_asset_info(self, asset_info):
        self._asset_info = asset_info
        if not asset_info:
            return

        self._original_version_id = asset_info.get("version_id")
        self._pending_version = None
        self._pending_action = None

        self._asset_name_label.setText(asset_info.get("asset_name") or "")

        # Pre-populate the version dropdown — suppress the staging callback
        # while the initial selection is being applied.
        self._handling_dropdown_signal = True
        try:
            available = asset_info.get("available_versions") or []
            if available:
                self._version_selector.setEnabled(True)
                self._version_selector.set_versions(available)
                for i in range(self._version_selector.count()):
                    item_data = self._version_selector.itemData(i)
                    if (
                        item_data
                        and item_data.get("id") == self._original_version_id
                    ):
                        self._version_selector.setCurrentIndex(i)
                        break
            else:
                # No version list available — show only the current vnum.
                self._version_selector.clear()
                version_number = asset_info.get("version_number")
                label = (
                    "v{}".format(version_number)
                    if version_number is not None
                    else "v?"
                )
                self._version_selector.addItem(label, None)
                self._version_selector.setEnabled(False)
        finally:
            self._handling_dropdown_signal = False

        self._user_date_label.setText(_format_user_and_date(asset_info))

        # Show just the component name (e.g. "image"); file_type is part of
        # the path/options and not interesting in the row header.
        self._component_label.setText(asset_info.get("component_name") or "")

        server_url = asset_info.get("server_url")
        if server_url:
            self._thumbnail_widget.set_server_url(server_url)
            thumbnail_url = asset_info.get("thumbnail_url")
            if thumbnail_url:
                self._thumbnail_widget.load(thumbnail_url)

        is_latest = asset_info.get("is_latest_version")
        if is_latest is True:
            self.set_status(constants.status.SUCCESS_STATUS, "Latest version")
        elif is_latest is False:
            self.set_status(
                constants.status.WARNING_STATUS,
                "A newer version is available",
            )
        else:
            self.set_status(constants.status.UNKNOWN_STATUS, "")

        # Pending state was reset above; reflect that on the row.
        self._refresh_pending_style()

        # Reflect ``objects_loaded`` on the row so the SCSS rule can mute
        # the asset name + secondary labels when the asset is a
        # placeholder. Use ``is False`` so a missing key defaults to
        # "loaded".
        unloaded = asset_info.get("objects_loaded") is False
        self.setProperty("unloaded", unloaded)
        self.style().unpolish(self)
        self.style().polish(self)
        # The thumbnail is dimmed via QGraphicsOpacityEffect — Qt
        # stylesheets don't support ``opacity`` on QWidgets, so the
        # SCSS-side rule alone is a no-op for the thumbnail.
        self._apply_unloaded_thumbnail_effect(unloaded)

    def _apply_unloaded_thumbnail_effect(self, unloaded):
        if self._thumbnail_widget is None:
            return
        if unloaded:
            effect = QtWidgets.QGraphicsOpacityEffect(self._thumbnail_widget)
            effect.setOpacity(0.25)
            self._thumbnail_widget.setGraphicsEffect(effect)
        else:
            # ``setGraphicsEffect(None)`` removes any previous effect
            # without leaking — Qt re-parents the old one for deletion.
            self._thumbnail_widget.setGraphicsEffect(None)

        # Force expanded content to rebuild next time it's opened.
        self._content_built = False
        if self._content_container is not None and isValid(
            self._content_container
        ):
            self._content_container.setParent(None)
            self._content_container.deleteLater()
        self._content_container = None

    # -- staging logic ---------------------------------------------------

    def has_pending_change(self):
        return (
            self._pending_version is not None
            or self._pending_action is not None
        )

    @property
    def pending_version(self):
        return self._pending_version

    @property
    def pending_action(self):
        """Returns ``"version"`` | ``"load"`` | ``"unload"`` | ``"remove"``
        | ``None``. ``"version"`` is set implicitly when a non-original
        version is in the dropdown; the others are set explicitly via
        ``stage_action``."""
        if self._pending_action is not None:
            return self._pending_action
        if self._pending_version is not None:
            return "version"
        return None

    def stage_action(self, action):
        """Stage a context-menu action (``"load"`` | ``"unload"`` |
        ``"remove"``) on this row. Mutually exclusive with a staged
        version change — staging an action reverts any dropdown change
        back to the original version."""
        if action not in ("load", "unload", "remove"):
            return
        # If the user previously staged a version change, snap the
        # dropdown back to the original version silently.
        if self._pending_version is not None:
            self._handling_dropdown_signal = True
            try:
                self._reset_dropdown_to_original()
            finally:
                self._handling_dropdown_signal = False
            self._pending_version = None
        was_pending = self._pending_action is not None
        self._pending_action = action
        self._refresh_pending_style()
        if not was_pending:
            self.pendingChanged.emit(True)

    def stage_update_to_latest(self):
        """Set the dropdown to this row's latest version. Triggers the
        existing version-staging logic via ``_on_version_selector_changed``
        — if the row is already on the latest version this is a no-op."""
        if not self._asset_info or self._version_selector is None:
            return
        available = self._asset_info.get("available_versions") or []
        latest_id = None
        for v in available:
            if v.get("is_latest_version"):
                latest_id = v.get("id")
                break
        if not latest_id:
            return
        for i in range(self._version_selector.count()):
            item_data = self._version_selector.itemData(i)
            if item_data and item_data.get("id") == latest_id:
                self._version_selector.setCurrentIndex(i)
                return

    def _reset_dropdown_to_original(self):
        if not self._version_selector or not self._original_version_id:
            return
        for i in range(self._version_selector.count()):
            item_data = self._version_selector.itemData(i)
            if item_data and item_data.get("id") == self._original_version_id:
                self._version_selector.setCurrentIndex(i)
                return

    def clear_pending_change(self):
        had = self.has_pending_change()
        self._pending_version = None
        self._pending_action = None
        if self._version_selector and self._original_version_id:
            self._handling_dropdown_signal = True
            try:
                self._reset_dropdown_to_original()
            finally:
                self._handling_dropdown_signal = False
        if had:
            self._refresh_pending_style()
            self.pendingChanged.emit(False)

    def _on_version_selector_changed(self, _index):
        if self._handling_dropdown_signal:
            return
        version_dict = self._version_selector.version
        if not version_dict:
            return
        new_id = version_dict.get("id")
        was_pending = self.has_pending_change()
        # User picked a version from the dropdown — mutually exclusive
        # with any staged context-menu action.
        self._pending_action = None
        if new_id == self._original_version_id:
            self._pending_version = None
            if was_pending:
                self._refresh_pending_style()
                self.pendingChanged.emit(False)
        else:
            self._pending_version = version_dict
            self._refresh_pending_style()
            if not was_pending:
                self.pendingChanged.emit(True)

    def _refresh_pending_style(self):
        """Push the current pending action onto the ``pending`` Qt
        property as a string value (or empty). SCSS reads it via
        ``AssetWidget[pending='version']`` etc."""
        self.setProperty("pending", self.pending_action or "")
        self.style().unpolish(self)
        self.style().polish(self)

    def _on_select_in_scene_clicked(self):
        if self._asset_info:
            self.selectInScene.emit(self._asset_info)

    # -- expanded content ------------------------------------------------

    def _populate_expanded_content(self):
        container = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(container)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(6)

        info = self._asset_info or {}

        self._add_section(
            layout,
            "Asset info",
            [
                ("Context path", info.get("context_path") or ""),
                ("Asset type", info.get("asset_type_name") or ""),
                ("Asset id", info.get("asset_id") or ""),
                ("Version id", info.get("version_id") or ""),
                ("Component id", info.get("component_id") or ""),
                ("Component name", info.get("component_name") or ""),
            ],
        )

        self._add_section(
            layout,
            "Load info",
            [
                ("Load mode", str(info.get("load_mode") or "")),
                ("Reference", str(info.get("reference_object") or "")),
                ("Objects loaded", str(info.get("objects_loaded"))),
                ("Is latest", str(info.get("is_latest_version"))),
            ],
        )

        layout.addWidget(LineWidget())
        dep_title = QtWidgets.QLabel("Dependencies")
        dep_title.setProperty("section_title", True)
        layout.addWidget(dep_title)
        deps = info.get("dependency_ids") or []
        if deps:
            for dep in deps:
                lbl = QtWidgets.QLabel("•  {}".format(dep))
                lbl.setProperty("secondary", True)
                lbl.setTextInteractionFlags(QtCore.Qt.TextSelectableByMouse)
                layout.addWidget(lbl)
        else:
            lbl = QtWidgets.QLabel("No dependencies")
            lbl.setProperty("secondary", True)
            layout.addWidget(lbl)

        layout.addWidget(LineWidget())
        opt_title = QtWidgets.QLabel("Raw options")
        opt_title.setProperty("section_title", True)
        layout.addWidget(opt_title)
        try:
            # FtrackAssetInfo.__getitem__ decodes the base64-encoded options
            # dict for us; .get() bypasses that hook, so use [] here.
            raw_options = (
                info["asset_info_options"]
                if info.get("asset_info_options")
                else {}
            )
            raw_text = json.dumps(raw_options, indent=2, sort_keys=True)
        except (TypeError, ValueError, KeyError):
            raw_text = str(info.get("asset_info_options") or "")
        raw_edit = QtWidgets.QTextEdit()
        raw_edit.setReadOnly(True)
        raw_edit.setPlainText(raw_text)
        raw_edit.setMaximumHeight(120)
        layout.addWidget(raw_edit)

        self.add_widget(container)
        self._content_container = container

    def _add_section(self, layout, title, rows):
        layout.addWidget(LineWidget())
        title_label = QtWidgets.QLabel(title)
        title_label.setProperty("section_title", True)
        layout.addWidget(title_label)

        form = QtWidgets.QFormLayout()
        form.setContentsMargins(8, 0, 0, 0)
        form.setHorizontalSpacing(12)
        form.setVerticalSpacing(2)
        for label_text, value in rows:
            label = QtWidgets.QLabel("{}:".format(label_text))
            label.setProperty("secondary", True)
            value_label = QtWidgets.QLabel(value)
            value_label.setTextInteractionFlags(
                QtCore.Qt.TextSelectableByMouse
            )
            form.addRow(label, value_label)
        layout.addLayout(form)

    # -- selection / search ----------------------------------------------

    def matches(self, search_text):
        if not search_text:
            return True
        if not self._asset_info:
            return False
        search_lower = search_text.lower()
        fields = [
            self._asset_info.get("context_path") or "",
            self._asset_info.get("asset_name") or "",
            self._asset_info.get("component_name") or "",
            self._asset_info.get("file_type") or "",
            self._asset_info.get("component_path") or "",
        ]
        return any(search_lower in (f or "").lower() for f in fields)

    def set_selected(self, selected):
        self._is_selected = selected
        self.setProperty("selected", bool(selected))
        self.style().unpolish(self)
        self.style().polish(self)

    def is_selected(self):
        return self._is_selected

    @property
    def asset_info(self):
        return self._asset_info
