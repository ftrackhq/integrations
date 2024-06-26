# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

try:
    from PySide6 import QtWidgets, QtCore
except ImportError:
    from PySide2 import QtWidgets, QtCore

from ftrack_qt.utils.widget import set_property
from ftrack_qt.widgets.buttons import CircularButton
from ftrack_qt.utils.layout import recursive_clear_layout


class SearchBox(QtWidgets.QFrame):
    '''
    Widget displaying a search box, that can be collapsed and expanded.
    '''

    inputUpdated = QtCore.Signal(object)  # User has update input
    clear = QtCore.Signal()  # Clear button was pressed

    @property
    def text(self):
        '''Retrieve the search text'''
        return self._input.text() if self._input else ''

    @text.setter
    def text(self, value):
        '''Set the search text to *value*'''
        if self._input:
            self._input.setText(value)

    def __init__(self, collapsed=True, collapsable=True, parent=None):
        '''
        Initialize the search widget

        :param collapsed: If True, search box should start collapsed (default)
        :param collapsable: If True, search can be collapsed by user.
        :param parent: The parent dialog or frame
        '''
        super(SearchBox, self).__init__(parent=parent)

        self._collapsed = collapsed
        self._collapsable = collapsable

        self._search_button = None
        self._input = None

        self.pre_build()
        self.build()
        self.post_build()

    def pre_build(self):
        '''Prepare general layout.'''
        self.setLayout(QtWidgets.QHBoxLayout(self))
        self.layout().setContentsMargins(4, 1, 5, 1)
        self.layout().setSpacing(1)
        self.setMaximumHeight(33)
        self.setMinimumHeight(33)

    def build(self):
        '''Build widgets and parent them.'''
        self.rebuild()

    def post_build(self):
        '''Post Build ui method for events connections.'''
        self._search_button.clicked.connect(self._on_search_clicked)

    def rebuild(self):
        '''Remove current widgets, clear input'''
        recursive_clear_layout(self.layout())
        set_property(self, 'collapsed', 'true' if self._collapsed else 'false')
        if self._collapsed:
            # Just the circular search button
            self.layout().addStretch()
            self._input = None
            self._search_button = CircularButton('search')
        else:
            self._search_button = CircularButton('search', diameter=26)

        if self._collapsable:
            self.layout().addWidget(self._search_button)

        if not self._collapsed:
            # A bordered input field filling all space, with input and a clear button
            self._input = QtWidgets.QLineEdit()
            self._input.setAttribute(QtCore.Qt.WA_MacShowFocusRect, False)
            self._input.setReadOnly(False)
            self._input.textChanged.connect(self._on_input_changed)
            self._input.setPlaceholderText("Type to search")
            self._input.setFocus()
            self.layout().addWidget(self._input, 100)
            if not self._collapsable:
                self.layout().addWidget(self._search_button)

    def _on_search_clicked(self):
        '''User clicked search button, update collapsed state'''
        if self._collapsable:
            self._collapsed = not self._collapsed
            self.rebuild()
            self.inputUpdated.emit('')

    def _on_input_changed(self):
        '''Search input text changed'''
        self.inputUpdated.emit(self._input.text())

    def _on_clear_clicked(self):
        '''Clear search input'''
        self._input.setText('')
        self._input.setFocus()
        self.clear.emit()
