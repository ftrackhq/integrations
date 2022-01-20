# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack
import functools
import platform

import qtawesome as qta

from Qt import QtWidgets, QtCore, QtCompat, QtGui

from ftrack_connect_pipeline import constants as core_const
from ftrack_connect_pipeline_qt.ui.utility.widget.search import Search
from ftrack_connect_pipeline_qt.ui.utility.widget.base.accordion_base import (
    AccordionBaseWidget,
)


class AssetManagerBaseWidget(QtWidgets.QWidget):
    '''Base widget of the asset manager and assembler'''

    @property
    def event_manager(self):
        '''Returns event_manager'''
        return self._event_manager

    @property
    def session(self):
        '''Returns Session'''
        return self.event_manager.session

    def init_header_content(self, layout):
        '''To be overridden by child'''
        layout.addStretch()

    @property
    def engine_type(self):
        '''Returns engine_type'''
        return self._engine_type

    @engine_type.setter
    def engine_type(self, value):
        '''Sets the engine_type with the given *value*'''
        self._engine_type = value

    def __init__(self, event_manager, parent=None):
        '''Initialise AssetManagerWidget with *event_manager*

        *event_manager* should be the
        :class:`ftrack_connect_pipeline.event.EventManager` instance to
        communicate to the event server.
        '''
        super(AssetManagerBaseWidget, self).__init__(parent=parent)

        self._event_manager = event_manager
        self._engine_type = None

        self.pre_build()
        self.build()
        self.post_build()

    def pre_build(self):
        '''Prepare general layout.'''
        self.setLayout(QtWidgets.QVBoxLayout(self))

    def build(self):
        '''Build widgets and parent them.'''

        self._header = QtWidgets.QWidget()
        self._header.setLayout(QtWidgets.QHBoxLayout())
        self.init_header_content(self._header.layout())
        self.layout().addWidget(self._header)

        self.scroll = QtWidgets.QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.layout().addWidget(self.scroll, 100)

    def post_build(self):
        '''Post Build ui method for events connections.'''
        pass

    def init_search(self):
        '''Create search box'''
        self._search = Search()
        self._search.input_updated.connect(self.on_search)
        return self._search

    def on_search(self, text):
        '''Search in the current model.'''
        pass


class AssetListModel(QtCore.QAbstractTableModel):
    '''Custom asset list model'''

    @property
    def session(self):
        return self._session

    def __init__(self, session):
        super(AssetListModel, self).__init__()
        self._session = session
        self.__asset_entities_list = []

    def rowCount(self, index=QtCore.QModelIndex):
        return len(self.__asset_entities_list)

    def columnCount(self, index=QtCore.QModelIndex):
        return 1

    def data(self, index, role=QtCore.Qt.DisplayRole):
        if role == QtCore.Qt.DisplayRole:
            return self.__asset_entities_list[index.row()]

    def insertRows(self, position, data, index=QtCore.QModelIndex):
        rows = len(data)
        self.beginInsertRows(QtCore.QModelIndex(), position, position + rows - 1)
        for row in range(rows):
            if position + row < len(self.__asset_entities_list):
                self.__asset_entities_list.insert(position + row, data[row])
            else:
                self.__asset_entities_list.append(data[row])
        self.endInsertRows()

    def reset(self):
        self.beginResetModel()
        self.__asset_entities_list = []
        self.endResetModel()

    def flags(self, index):
        if not index.isValid():
            return QtCore.Qt.ItemIsEnabled
        return (
            QtCore.Qt.ItemFlags(QtCore.QAbstractTableModel.flags(self, index))
            | QtCore.Qt.ItemIsEditable
        )


class AssetListWidget(QtWidgets.QWidget):
    '''Custom asset list view'''

    _last_clicked = None

    @property
    def model(self):
        return self._model

    @property
    def assets(self):
        for i in range(self.layout().count()):
            widget = self.layout().itemAt(i).widget()
            if widget and isinstance(widget, AccordionBaseWidget):
                yield widget

    def __init__(self, model, asset_widget_class, parent=None):
        super(AssetListWidget, self).__init__(parent=parent)
        self._model = model
        self._asset_widget_class = asset_widget_class
        self.was_clicked = False

        self.pre_build()
        self.build()
        self.post_build()

    def pre_build(self):
        self.setLayout(QtWidgets.QVBoxLayout())
        self.layout().setContentsMargins(1, 1, 1, 1)
        self.layout().setSpacing(1)

    def build(self):
        pass

    def post_build(self):
        self._model.rowsInserted.connect(self.on_assets_added)
        self._model.modelReset.connect(self.rebuild)

    def on_assets_added(self, parent, first, last):
        self.rebuild()

    def rebuild(self):
        '''Clear widget and add all assets again from model.'''
        for widget in reversed(list(self.assets)):
            widget.setParent(None)
            widget.deleteLater()
        # TODO: Save selection state
        for row in range(self.model.rowCount()):
            asset_widget = self._asset_widget_class(
                self.model.createIndex(row, 0, self.model), self.model.session
            )
            asset_info = self.model.data(asset_widget.index)
            asset_widget.set_asset_info(asset_info)
            self.layout().addWidget(asset_widget)
            asset_widget.clicked.connect(
                functools.partial(self.asset_clicked, asset_widget)
            )

    def reset(self):
        '''Remove all assets'''
        self.model.reset()
        self.rebuild()

    def selection(self, warn_on_empty=True):
        result = []
        for widget in self.assets:
            if widget.selected:
                result.append(self.model.data(widget.index))
        if warn_on_empty and len(result) == 0:
            QtWidgets.QMessageBox.critical(
                None,
                'Error!',
                "Please select at least one asset!",
                QtWidgets.QMessageBox.Abort,
            )
        return result

    def clear_selection(self):
        for asset_widget in self.assets:
            asset_widget.set_selected(False)

    def asset_clicked(self, asset_widget, event):
        '''An asset (accordion) were clicked in list, evaluate selection.'''
        modifiers = QtWidgets.QApplication.keyboardModifiers()
        if event.button() == QtCore.Qt.RightButton:
            return
        if (modifiers == QtCore.Qt.Key_Meta and platform.system() != 'Darwin') or (
            modifiers == QtCore.Qt.ControlModifier and platform.system() == 'Darwin'
        ):
            # Add to selection
            pass
        elif modifiers == QtCore.Qt.ShiftModifier:
            # Select inbetweens
            if self._last_clicked:
                start_row = min(
                    self._last_clicked.index.row(), asset_widget.index.row()
                )
                end_row = max(self._last_clicked.index.row(), asset_widget.index.row())
                for widget in self.assets:
                    if start_row < widget.index.row() < end_row:
                        widget.set_selected(True)
        else:
            self.clear_selection()
        asset_widget.set_selected(True)
        self._last_clicked = asset_widget

    def mousePressEvent(self, event):
        # Consume this event, so parent client does not de-select all
        pass
