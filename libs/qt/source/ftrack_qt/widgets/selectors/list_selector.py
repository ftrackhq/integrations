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

    _last_clicked = None  # The item last clicked, used for SHIFT+ selections

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
        Initialize item list widget

        :param model: :class:`QtCore.QAbstractTableModel` instance
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
            item_widget = self._item_factory(index, item_data)
            assert isinstance(item_widget, ListSelectorItem), (
                'Item factory must return a widget that inherits from '
                'ListSelectorItem'
            )
            # Styling:
            set_property(item_widget, 'first', 'true' if row == 0 else 'false')
            self.layout().addWidget(item_widget)
            item_widget.clicked.connect(
                partial(self.item_clicked, item_widget)
            )
        # Filler
        self.layout().addWidget(QtWidgets.QWidget(), 100)
        self.refresh()
        self.rebuilt.emit()

    def refresh(self, search_text=None):
        '''Update list depending on search text'''
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
        '''Return list of data items, or item widgets if *as_widgets* is True'''
        result = []
        for widget in self.items:
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
        '''De-select all items'''
        if not shiboken2.isValid(self):
            return
        selection_item_data_changed = False
        for item_widget in self.items:
            if item_widget.selected:
                item_widget.selected = False
                selection_item_data_changed = True
        if selection_item_data_changed:
            selection = self.selection()
            if selection is not None:
                self.selection_updated.emit(selection)

    def item_clicked(self, item_widget, event):
        '''An item were clicked in list, evaluate selection.'''
        selection_item_data_changed = False
        modifiers = QtWidgets.QApplication.keyboardModifiers()
        if event.button() == QtCore.Qt.RightButton:
            # Select the current if nothing is selected
            if len(self.selection()) == 0:
                item_widget.selected = True
                selection_item_data_changed = True
        elif (
            modifiers == QtCore.Qt.Key_Meta and platform.system() != 'Darwin'
        ) or (
            modifiers == QtCore.Qt.ControlModifier
            and platform.system() == 'Darwin'
        ):
            # Toggle selection
            if not item_widget.selected:
                if not item_widget.selected:
                    item_widget.selected = True
                    selection_item_data_changed = True
            else:
                if not item_widget.selected:
                    item_widget.selected = False
                    selection_item_data_changed = True
        elif modifiers == QtCore.Qt.ShiftModifier:
            # Select in betweens
            if self._last_clicked:
                start_row = min(
                    self._last_clicked.index.row(), item_widget.index.row()
                )
                end_row = max(
                    self._last_clicked.index.row(), item_widget.index.row()
                )
                for widget in self.items:
                    if start_row <= widget.index.row() <= end_row:
                        if not widget.selected:
                            widget.selected = True
                            selection_item_data_changed = True
        else:
            self.clear_selection()
            if not item_widget.selected:
                item_widget.selected = True
                selection_item_data_changed = True
        self._last_clicked = item_widget
        if selection_item_data_changed:
            selection = self.selection()
            if selection is not None:
                self.selection_updated.emit(selection)

    def get_widget(self, index):
        '''Return the item widget representation at *index*'''
        for widget in self.items:
            if widget.index.row() == index.row():
                return widget

    def mousePressEvent(self, event):
        '''(Override) Consume this event, so parent client does not de-select all'''
        pass


class ListSelectorItem(object):
    '''Base class for an item in the list selector.'''

    clicked = QtCore.Signal(object)
    # Emitted when item is clicked

    double_clicked = QtCore.Signal(
        object
    )  # Emitted when item is double-clicked

    @property
    def index(self):
        '''Return the index this item has in list'''
        return self._index

    @index.setter
    def index(self, value):
        '''Set the index this item has in list'''
        self._index = value

    @property
    def selected(self):
        '''Return if item is selected or not'''
        return self._selected

    @selected.setter
    def selected(self, value):
        '''Set if item is selected or not'''
        self._selected = value

    # TODO This should be an ABC
    def matches(self, text):
        '''Return True if this item matches *text*'''
        raise NotImplementedError()

    def __init__(self, index):
        self._index = index
        self._selected = False
