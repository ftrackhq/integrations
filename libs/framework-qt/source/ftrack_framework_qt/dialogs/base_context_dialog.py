# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

from Qt import QtWidgets, QtCore

from ftrack_framework_widget.dialog import FrameworkDialog

from ftrack_qt.widgets.dialogs import StyledDialog
from ftrack_qt.widgets.headers import SessionHeader
from ftrack_qt.widgets.selectors import ContextSelector

from ftrack_qt.utils.layout import recursive_clear_layout
from ftrack_qt.utils.decorators import invoke_in_qt_main_thread

import ftrack_constants.framework as constants


class BaseContextDialog(FrameworkDialog, StyledDialog):
    '''Default Framework Publisher dialog'''

    name = 'base_context_dialog'
    tool_config_type_filter = None
    run_button_title = 'run'
    ui_type = 'qt'
    docked = True

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

    @property
    def progress_widget(self):
        '''Return the progress widget of the dialog'''
        return self._progress_widget

    @progress_widget.setter
    def progress_widget(self, value):
        '''Set the progress widget of the dialog'''
        self._progress_widget = value

    @property
    def header(self):
        return self._header

    @property
    def tool_widget(self):
        return self._tool_widget

    @property
    def run_button(self):
        return self._run_button

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
        Initialize Mixin class publisher dialog. It will load the qt dialog and
        mix it with the framework dialog.
        *event_manager*: instance of
        :class:`~ftrack_framework_core.event.EventManager`
        *client_id*: Id of the client that initializes the current dialog
        *connect_methods_callback*: Client callback method for the dialog to be
        able to execute client methods.
        *connect_setter_property_callback*: Client callback property setter for
        the dialog to be able to read client properties.
        *connect_getter_property_callback*: Client callback property getter for
        the dialog to be able to write client properties.
        *dialog_options*: Dictionary of arguments passed to configure the
        current dialog.
        '''
        # As a mixing class we have to initialize the parents separately
        StyledDialog.__init__(
            self,
            background_style=None,
            docked=self.docked,
            parent=parent,
        )
        FrameworkDialog.__init__(
            self,
            event_manager,
            client_id,
            connect_methods_callback,
            connect_setter_property_callback,
            connect_getter_property_callback,
            dialog_options,
            parent,
        )
        self._header = None
        self._context_selector = None
        self._progress_widget = None
        self._tool_widget = None
        self._run_button = None

        self.pre_build()
        self.build()
        self.post_build()

    def pre_build(self):
        main_layout = QtWidgets.QVBoxLayout()
        self.setLayout(main_layout)

    def build(self):
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
        self.layout().addWidget(self._context_selector, QtCore.Qt.AlignTop)
        self.layout().addWidget(self._tool_widget)
        self.layout().addWidget(self._run_button)

    def post_build(self):
        '''Set up all the signals'''
        self._on_client_context_changed_callback()

        # Connect context selector signals
        self._context_selector.context_changed.connect(
            self._on_context_selected_callback
        )
        # Connect run_tool_config button
        self._run_button.clicked.connect(self._on_run_button_clicked)

    def _on_context_selected_callback(self, context_id):
        '''Emit signal with the new context_id'''
        if not context_id:
            return
        self.context_id = context_id

    def _on_client_context_changed_callback(self, event=None):
        '''Client context has been changed'''
        super(BaseContextDialog, self)._on_client_context_changed_callback(
            event
        )
        self.selected_context_id = self.context_id
        # Clean the UI every time a new context is set as the current tool
        # config might not be available anymore
        self.clean_ui()
        self.pre_build_ui()
        self.build_ui()
        self.post_build_ui()

    def _on_run_button_clicked(self):
        '''
        Run button from the UI has been clicked.
        Tell client to run the current tool config
        '''
        if self.progress_widget:
            self.progress_widget.run(self, self._run_button.text())
        self.run_tool_config(self.tool_config['reference'])

    @invoke_in_qt_main_thread
    def plugin_run_callback(self, log_item):
        '''(Override) Pass framework log item to the progress widget'''
        if self.progress_widget:
            self.progress_widget.update_framework_progress(log_item)

    # FrameworkDialog overrides
    def show_ui(self):
        '''Override Show method of the base framework dialog'''
        StyledDialog.show(self)
        self.raise_()
        self.activateWindow()
        self.setWindowState(
            self.windowState() & ~QtCore.Qt.WindowMinimized
            | QtCore.Qt.WindowActive
        )

    def connect_focus_signal(self):
        '''Connect signal when the current dialog gets focus'''
        pass

    def sync_context(self):
        '''
        Client context has been changed and doesn't match the ui context when
        focus is back to the current UI
        '''
        pass

    def _on_tool_config_changed_callback(self):
        '''The selected tool config has been changed'''
        pass

    def sync_host_connection(self):
        pass

    def clean_ui(self):
        removed_widgets = []
        recursive_clear_layout(self._tool_widget.layout(), removed_widgets)
        for widget in removed_widgets:
            if not hasattr(widget, 'name'):
                continue
            self.unregister_widget(widget.name)

    def pre_build_ui(self):
        raise NotImplementedError

    def build_ui(self):
        raise NotImplementedError

    def post_build_ui(self):
        raise NotImplementedError
