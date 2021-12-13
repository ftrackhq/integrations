# :coding: utf-8
# :copyright: Copyright (c) 2014-2021 ftrack
import qtawesome as qta

from Qt import QtGui, QtCore, QtWidgets

from ftrack_connect_pipeline_qt import utils
from ftrack_connect_pipeline_qt.ui.utility.widget.circular_button import CircularButton

class Search(QtWidgets.QFrame):
    '''
    Display a search box, that can be collapsed and expanded.
    '''
    input_updated = QtCore.Signal(object)
    search = QtCore.Signal()
    clear = QtCore.Signal()

    def __init__(self, parent=None, collapsed=True):
        super(Search, self).__init__(parent=parent)

        self._collapsed = collapsed

        self.pre_build()
        self.build()
        self.post_build()

    def pre_build(self):
        '''Prepare general layout.'''
        self.setLayout(QtWidgets.QHBoxLayout(self))
        self.layout().setContentsMargins(1, 1, 1, 1)
        self.layout().setSpacing(1)
        self.setMaximumHeight(32)
        self.setMinimumHeight(32)

    def build(self):
        '''Build widgets and parent them.'''
        self.rebuild()

    def post_build(self):
        '''Post Build ui method for events connections.'''
        pass

    def rebuild(self):
        # Remove current widgets, clear input
        for i in reversed(range(self.layout().count())):
            widget = self.layout().itemAt(i).widget()
            if widget:
                widget.setParent(None)
        if self._collapsed:
            # Just the circular search button
            self.layout().addStretch()
            self._input = None
            self.setStyleSheet('''border:none;''')
            self._search_button = CircularButton('magnify', '#999999')
            self._search_button.setStyleSheet('''
                border: 1px solid #1A1A1A;
                border-radius: 16px;
            ''')
        else:
            self._search_button = CircularButton('magnify', '#999999', diameter=30)

        self._search_button.clicked.connect(self._on_search)
        self.layout().addWidget(self._search_button)

        if not self._collapsed:
            # A bordered input field filling all space, with input and a clear button
            self._search_button.setStyleSheet('''border:none;''')
            self._input = QtWidgets.QLineEdit()
            self._input.textChanged.connect(self._on_input_changed)
            self._input.setStyleSheet('border: none;')
            self._input.setFocus()
            self.layout().addWidget(self._input, 100)
            self._clear_button = CircularButton('close', '#1A1A1A', diameter=30)
            self._clear_button.setStyleSheet('''border:none;''')
            self._clear_button.clicked.connect(self._on_clear)
            self.layout().addWidget(self._clear_button)
            self.setStyleSheet('''
                border: 1px solid #1A1A1A;
                border-radius: 16px;
            ''')

    def _on_search(self):
        self._collapsed = not self._collapsed
        self.rebuild()

    def _on_input_changed(self):
        self.input_updated.emit(self._input.text())

    def _on_clear(self):
        self._input.setText('')
        self._input.setFocus()
        self.clear.emit()
