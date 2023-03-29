# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack

from Qt import QtGui, QtCore, QtWidgets

from ftrack_connect_pipeline_qt import utils
from ftrack_connect_pipeline_qt.ui.utility.widget.circular_button import (
    CircularButton,
)
from ftrack_connect_pipeline_qt.utils import clear_layout


class Search(QtWidgets.QFrame):
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
        super(Search, self).__init__(parent=parent)

        self._collapsed = collapsed
        self._collapsable = collapsable
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
        clear_layout(self.layout())
        if self._collapsed:
            # Just the circular search button
            self.layout().addStretch()
            self._input = None
            self.setStyleSheet('''border:none;''')
            self._search_button = CircularButton('search')
            self._search_button.setStyleSheet(
                '''
                border: 1px solid #2A2A2A;
                border-radius: 16px;
            '''
            )
        else:
            self._search_button = CircularButton('search', diameter=30)

        if self._collapsable:
            self.layout().addWidget(self._search_button)

        if not self._collapsed:
            # A bordered input field filling all space, with input and a clear button
            self._search_button.setStyleSheet(
                '''
                    border:none; 
                    background: transparent;
                '''
            )
            self._input = QtWidgets.QLineEdit()
            self._input.setReadOnly(False)
            self._input.textChanged.connect(self._on_input_changed)
            self._input.setPlaceholderText("Type to search")
            self._input.setStyleSheet(
                '''border: none; background: transparent; '''
            )
            self._input.setFocus()
            self.layout().addWidget(self._input, 100)

            self.setStyleSheet(
                '''
                border: 1px solid #555555;
                border-radius: 16px;
            '''
            )
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
