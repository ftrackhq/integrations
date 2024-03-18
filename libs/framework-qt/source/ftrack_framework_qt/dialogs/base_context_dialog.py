# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

try:
    from PySide6 import QtWidgets, QtCore
except ImportError:
    from PySide2 import QtWidgets, QtCore

from ftrack_framework_qt.dialogs.base_dialog import BaseDialog

from ftrack_qt.widgets.headers import SessionHeader
from ftrack_qt.widgets.selectors import ContextSelector


class BaseContextDialog(BaseDialog):
    '''Default Framework Publisher dialog'''

    name = 'base_context_dialog'
    tool_config_type_filter = None
    run_button_title = 'run'
    ui_type = 'qt'

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
        event_manager,
        client_id,
        connect_methods_callback,
        connect_setter_property_callback,
        connect_getter_property_callback,
        dialog_options,
        parent=None,
    ):
        '''
        Overrides BaseDialog class and implements context selector logic
        '''

        self._context_selector = None

        super(BaseContextDialog, self).__init__(
            event_manager,
            client_id,
            connect_methods_callback,
            connect_setter_property_callback,
            connect_getter_property_callback,
            dialog_options,
            parent=parent,
        )

    def build(self):
        '''Re implement the build method to contain context selector'''

        # Create the header
        self._header = SessionHeader(self.event_manager.session)

        self._context_selector = ContextSelector(
            self.event_manager.session, enable_context_change=True
        )

        self._tool_widget = QtWidgets.QWidget()
        _tool_widget_layout = QtWidgets.QVBoxLayout()
        self._tool_widget.setLayout(_tool_widget_layout)

        self._run_button = QtWidgets.QPushButton(self.run_button_title)

        self.layout().addWidget(self._header)
        self.layout().addWidget(
            self._context_selector,
            QtCore.Qt.AlignmentFlag.AlignTop,
        )
        self.layout().addWidget(self._tool_widget)
        self.layout().addWidget(self._run_button)

    def post_build(self):
        '''Override the post_build method to create context selector signals'''
        super(BaseContextDialog, self).post_build()
        # Connect context selector signals
        self._context_selector.context_changed.connect(
            self._on_context_selected_callback
        )

    def _on_context_selected_callback(self, context_id):
        '''Emit signal with the new context_id'''
        if not context_id:
            return
        self.context_id = context_id

    def _on_client_context_changed_callback(self, event=None):
        '''Client context has been changed'''
        self.selected_context_id = self.context_id
        super(BaseContextDialog, self)._on_client_context_changed_callback(
            event
        )
