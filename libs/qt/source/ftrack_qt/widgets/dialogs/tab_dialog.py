# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

from Qt import QtWidgets, QtCore

from ftrack_qt.widgets.selectors import ListSelector
from ftrack_qt.widgets.headers import SessionHeader
from ftrack_qt.widgets.selectors import ContextSelector

from ftrack_qt.widgets.dialogs import StyledDialog


class TabDialog(StyledDialog):
    '''Base Class to represent a Plugin'''

    selected_context_changed = QtCore.Signal(object)
    selected_tab_changed = QtCore.Signal(object)

    @property
    def selected_context_id(self):
        '''Return the selected context id in the context selector'''
        return self._context_selector.context_id

    @selected_context_id.setter
    def selected_context_id(self, value):
        '''Set the given *value* as the selected context id'''
        if self.selected_context_id != value:
            self._context_selector.context_id = value

    @property
    def is_browsing_context(self):
        '''
        Return if context selector is currently working on setting up a context
        '''
        return self._context_selector.is_browsing

    def __init__(
        self,
        session,
        parent=None,
    ):
        '''
        Initialise BasePlugin with instance of
        :class:`ftrack_api.session.Session`
        '''
        super(TabDialog, self).__init__(parent=parent)

        self._session = session
        self._context_selector = None
        self._tab_widget = None
        self._header = None

        self.pre_build()
        self.build()
        self.post_build()

    def pre_build(self):
        main_layout = QtWidgets.QVBoxLayout()
        self.setLayout(main_layout)

    def build(self):
        # Create the header
        self._header = SessionHeader(self._session)
        # TODO: implement progress widget.
        # self._progress_widget = ProgressWidget
        # self._header.add_widget(self._progress_widget)

        # TODO: we have to update the signals from the context selector to
        #  identify that are our signals and not qt signals. So make them snake case
        self._context_selector = ContextSelector(
            self._session, enable_context_change=True
        )

        self._tab_widget = QtWidgets.QTabWidget()

        self.layout().addWidget(self._header)
        self.layout().addWidget(self._context_selector, QtCore.Qt.AlignTop)
        self.layout().addWidget(self._tab_widget)

    def post_build(self):
        '''Set up all the signals'''
        # Connect context selector signals
        self._context_selector.context_changed.connect(
            self._on_context_selected_callback
        )
        # Connect tab widget
        self._tab_widget.currentChanged.connect(self._on_tab_changed_callback)

    def add_tab(self, tab_title, widget):
        self._tab_widget.addTab(widget, tab_title)

    def _on_context_selected_callback(self, context_id):
        '''Emit signal with the new context_id'''
        if not context_id:
            return
        self.selected_context_changed.emit(context_id)

    def _on_tab_changed_callback(self, index):
        self.selected_tab_changed.emit(self._tab_widget.tabText(index))

    def clear_tab_ui(self):
        '''Remove all widgets from the tabs layout'''
        self._tab_widget.currentChanged.disconnect()
        while self._tab_widget.count():
            widget = self._tab_widget.widget(0)
            self._tab_widget.removeTab(0)
            if widget:
                widget.deleteLater()
        self._tab_widget.currentChanged.connect(self._on_tab_changed_callback)
