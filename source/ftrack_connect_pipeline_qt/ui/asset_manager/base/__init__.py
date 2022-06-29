# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack
import platform

from Qt import QtWidgets, QtCore
import shiboken2

from ftrack_connect_pipeline_qt.ui.utility.widget.search import Search
from ftrack_connect_pipeline_qt.ui.utility.widget.base.accordion_base import (
    AccordionBaseWidget,
)
from ftrack_connect_pipeline_qt.ui.utility.widget import scroll_area


class AssetManagerBaseWidget(QtWidgets.QWidget):
    '''Base widget of the asset manager'''

    @property
    def event_manager(self):
        '''Returns event_manager'''
        return self._event_manager

    @property
    def session(self):
        '''Returns Session'''
        return self.event_manager.session

    @property
    def engine_type(self):
        '''Returns engine_type'''
        return self._engine_type

    @engine_type.setter
    def engine_type(self, value):
        '''Sets the engine_type with the given *value*'''
        self._engine_type = value

    def __init__(
        self, is_assembler, event_manager, asset_list_model, parent=None
    ):
        '''
        Initialize asset manager widget

        :param is_assembler: Boolean telling if this asset manager is docked in assembler (True) or in DCC (False)
        :param event_manager:  :class:`~ftrack_connect_pipeline.event.EventManager` instance
        :param asset_list_model: : instance of :class:`~ftrack_connect_pipeline_qt.ui.asset_manager.model.AssetListModel`
        :param parent: the parent dialog or frame
        '''
        super(AssetManagerBaseWidget, self).__init__(parent=parent)

        self._is_assembler = is_assembler
        self._event_manager = event_manager
        self._asset_list_model = asset_list_model
        self._engine_type = None

        self.pre_build()
        self.build()
        self.post_build()

    def pre_build(self):
        '''Prepare general layout.'''
        self.setLayout(QtWidgets.QVBoxLayout(self))
        self.layout().setContentsMargins(0, 0, 0, 0)
        self.layout().setSpacing(0)

    def build_header(self, layout):
        '''Build the asset manager header and add to *layout*. To be overridden by child'''
        layout.addStretch()

    def build(self):
        '''Build widgets and parent them.'''
        self._header = QtWidgets.QWidget()
        self._header.setLayout(QtWidgets.QVBoxLayout())
        self._header.layout().setContentsMargins(1, 1, 1, 10)
        self._header.layout().setSpacing(4)
        self.build_header(self._header.layout())
        self.layout().addWidget(self._header)

        self.scroll = scroll_area.ScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.layout().addWidget(self.scroll, 100)

    def post_build(self):
        '''Post Build ui method for events connections.'''
        pass

    def init_search(self):
        '''Create search input'''
        self._search = Search(
            collapsed=self._is_assembler, collapsable=self._is_assembler
        )
        self._search.inputUpdated.connect(self.on_search)
        return self._search

    def on_search(self, text):
        '''Search in the current model, to be implemented by child.'''
        pass


class AssetListWidget(QtWidgets.QWidget):
    '''Generic asset list view widget'''

    _last_clicked = None  # The asset last clicked, used for SHIFT+ selections

    selectionUpdated = QtCore.Signal(
        object
    )  # Emitted when selection has been updated
    refreshed = QtCore.Signal()  # Should be emitted when list has been rebuilt

    @property
    def model(self):
        return self._model

    @property
    def assets(self):
        '''Return assets added to widget'''
        for i in range(self.layout().count()):
            widget = self.layout().itemAt(i).widget()
            if widget and isinstance(widget, AccordionBaseWidget):
                yield widget

    def __init__(self, model, parent=None):
        '''
        Initialize asset list widget

        :param model: :class:`~ftrack_connect_pipeline_qt.ui.asset_manager.model.AssetListModel` instance
        :param parent:  The parent dialog or frame
        '''
        super(AssetListWidget, self).__init__(parent=parent)
        self._model = model
        self.was_clicked = False

        self.pre_build()
        self.build()
        self.post_build()

    def pre_build(self):
        self.setLayout(QtWidgets.QVBoxLayout())
        self.layout().setContentsMargins(0, 0, 0, 0)
        self.layout().setSpacing(0)

    def build(self):
        pass

    def post_build(self):
        pass

    def rebuild(self):
        '''Clear widget and add all assets again from model. Should be overridden by child'''
        raise NotImplementedError()

    def selection(self, as_widgets=False):
        '''Return list of asset infos or asset widgets if *as_widgets* is True'''
        result = []
        for widget in self.assets:
            if widget.selected:
                if as_widgets:
                    result.append(widget)
                else:
                    data = self.model.data(widget.index)
                    if data is None:
                        # Data has changed
                        return None
                    result.append(data)
        return result

    def clear_selection(self):
        '''De-select all assets'''
        if not shiboken2.isValid(self):
            return
        selection_asset_data_changed = False
        for asset_widget in self.assets:
            if asset_widget.set_selected(False):
                selection_asset_data_changed = True
        if selection_asset_data_changed:
            selection = self.selection()
            if selection is not None:
                self.selectionUpdated.emit(selection)

    def asset_clicked(self, asset_widget, event):
        '''An asset were clicked in list, evaluate selection.'''
        selection_asset_data_changed = False
        modifiers = QtWidgets.QApplication.keyboardModifiers()
        if event.button() == QtCore.Qt.RightButton:
            return
        if (
            modifiers == QtCore.Qt.Key_Meta and platform.system() != 'Darwin'
        ) or (
            modifiers == QtCore.Qt.ControlModifier
            and platform.system() == 'Darwin'
        ):
            # Toggle selection
            if not asset_widget.selected:
                if asset_widget.set_selected(True):
                    selection_asset_data_changed = True
            else:
                if asset_widget.set_selected(False):
                    selection_asset_data_changed = True
        elif modifiers == QtCore.Qt.ShiftModifier:
            # Select inbetweens
            if self._last_clicked:
                start_row = min(
                    self._last_clicked.index.row(), asset_widget.index.row()
                )
                end_row = max(
                    self._last_clicked.index.row(), asset_widget.index.row()
                )
                for widget in self.assets:
                    if start_row <= widget.index.row() <= end_row:
                        if widget.set_selected(True):
                            selection_asset_data_changed = True
        else:
            self.clear_selection()
            if asset_widget.set_selected(True):
                selection_asset_data_changed = True
        self._last_clicked = asset_widget
        if selection_asset_data_changed:
            selection = self.selection()
            if selection is not None:
                self.selectionUpdated.emit(selection)

    def get_widget(self, index):
        '''Return the asset widget representation at *index*'''
        for widget in self.assets:
            if widget.index.row() == index.row():
                return widget

    def mousePressEvent(self, event):
        '''Consume this event, so parent client does not de-select all'''
        pass
