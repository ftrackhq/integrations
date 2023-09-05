# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack
import platform
import shiboken2
from functools import partial

from Qt import QtWidgets, QtCore

from ftrack_qt.utils.widget import clear_layout, set_property


class ListSelector(QtWidgets.QWidget):
    '''Generic searchable list widget extending the capabilities and mitigating shortcomings
    of QListWidget. Used when listing complex items in a list such as DCC assets and
    assembler components for load.'''

    _last_clicked = None  # The asset last clicked, used for SHIFT+ selections

    selection_updated = QtCore.Signal(
        object
    )  # Emitted when selection has been updated
    rebuilt = QtCore.Signal()  # Emitted when list has been rebuilt

    @property
    def model(self):
        return self._model

    @property
    def items(self):
        '''Return all items in list'''
        for i in range(self.layout().count()):
            widget = self.layout().itemAt(i).widget()
            if widget and isinstance(widget, ListSelectorItem):
                yield widget

    def __init__(self, model, item_factory, parent=None):
        '''
        Initialize asset list widget

        :param model: :class:`~ftrack_qt.model.asset_list.AssetListModel` instance
        :param item_factory: function that should return a widget for each item in model,
            must inherit from :class:`~ftrack_qt.widgets.selectors.ListSelectorItem` and QWidget.
        :param parent:  The parent dialog or frame
        '''
        super(ListSelector, self).__init__(parent=parent)
        self._model = model
        self._item_factory = item_factory

        self.was_clicked = False
        self.prev_search_text = ''

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
        self._model.rowsInserted.connect(self.rebuild)
        self._model.modelReset.connect(self.rebuild)
        self._model.rowsRemoved.connect(self.rebuild)
        self._model.dataChanged.connect(self.rebuild)

    def rebuild(self, *args):
        '''Clear widget and add all items from model'''
        clear_layout(self.layout())
        # TODO: Save selection state
        for row in range(self.model.rowCount()):
            index = self.model.createIndex(row, 0, self.model)
            item_data = self.model.data(index)
            item_widget = self._item_factory(
                index, item_data
            )
            set_property(
                item_widget, 'first', 'true' if row == 0 else 'false'
            )
            self.layout().addWidget(item_widget)
            item_widget.clicked.connect(
                partial(self.asset_clicked, item_widget)
            )
        self.refresh()
        self.rebuilt.emit()

    def refresh(self, search_text=None):
        '''Update asset list depending on search text'''
        if search_text is None:
            search_text = self.prev_search_text
        for item_widget in self.items:
            item_widget.setVisible(
                len(search_text) == 0 or item_widget.matches(search_text)
            )

    def on_search(self, text):
        '''Callback on change of user search input'''
        if text != self.prev_search_text:
            self.refresh(text.lower())
            self.prev_search_text = text

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
            # Select in betweens
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
        '''(Override) Consume this event, so parent client does not de-select all'''
        pass


class ListSelectorItem(object):
    ''' Base class for an item in the list selector. '''

    #TODO This should be an ABC
    def matches(self, text):
        '''Return True if this item matches *text*'''
        raise NotImplementedError()

    def __init__(self):
        self.selected = False