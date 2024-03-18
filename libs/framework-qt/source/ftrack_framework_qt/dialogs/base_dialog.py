# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

try:
    from PySide6 import QtWidgets, QtCore

    is_pyside6 = True
except ImportError:
    from PySide2 import QtWidgets, QtCore

    is_pyside6 = False
from ftrack_framework_core.widget.dialog import FrameworkDialog

from ftrack_qt.widgets.dialogs import StyledDialog
from ftrack_qt.widgets.headers import SessionHeader

from ftrack_qt.utils.layout import recursive_clear_layout


class BaseDialog(FrameworkDialog, StyledDialog):
    '''Default Framework dialog'''

    name = 'base_dialog'
    tool_config_type_filter = None
    run_button_title = 'run'
    ui_type = 'qt'

    @property
    def header(self):
        return self._header

    @property
    def tool_widget(self):
        return self._tool_widget

    @property
    def run_button(self):
        return self._run_button

    @property
    def tool_config_names(self):
        '''Return tool config names if passed in the dialog options.'''
        return self.dialog_options.get('tool_config_names')

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
            docked=dialog_options.get("docked", False),
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

        self._tool_widget = QtWidgets.QWidget()
        _tool_widget_layout = QtWidgets.QVBoxLayout()
        self._tool_widget.setLayout(_tool_widget_layout)

        self._run_button = QtWidgets.QPushButton(self.run_button_title)

        self.layout().addWidget(self._header)
        self.layout().addWidget(self._tool_widget)
        self.layout().addWidget(self._run_button)

    def post_build(self):
        '''Set up all the signals'''
        self._on_client_context_changed_callback()
        # Connect run_tool_config button
        self._run_button.clicked.connect(self._on_run_button_clicked)

    def _on_client_context_changed_callback(self, event=None):
        '''Client context has been changed'''
        super(BaseDialog, self)._on_client_context_changed_callback(event)
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

        self.run_tool_config(self.tool_config['reference'])

    # FrameworkDialog overrides
    def show_ui(self):
        '''Override Show method of the base framework dialog'''
        StyledDialog.show(self)
        self.raise_()
        self.activateWindow()
        if is_pyside6:
            self.setWindowState(
                self.windowState() & ~QtCore.Qt.WindowState.WindowMinimized
                | QtCore.Qt.WindowState.WindowActive
            )
        else:
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

    def closeEvent(self, event):
        self.ui_closed()
        super(BaseDialog, self).closeEvent(event)
