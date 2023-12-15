# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

from Qt import QtWidgets, QtCore

from ftrack_framework_widget.dialog import FrameworkDialog

from ftrack_qt.widgets.dialogs import StyledDialog

from ftrack_qt.utils.layout import recursive_clear_layout


class BaseDialog(FrameworkDialog, StyledDialog):
    '''Default Framework dialog'''

    name = 'base_dialog'
    tool_config_type_filter = None
    ui_type = 'qt'
    docked = True

    @property
    def tool_widget(self):
        return self._tool_widget

    def __init__(
        self,
        event_manager,
        client_id,
        connect_methods_callback,
        connect_setter_property_callback,
        connect_getter_property_callback,
        tool_config_names,
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
        *tool_config_names*: List of tool config names to pass on to the dialog
        *tool_config_names*: Dictionary of arguments passed to configure the
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
            tool_config_names,
            dialog_options,
            parent=parent,
        )
        self._tool_widget = None

        self.pre_build()
        self.build()
        self.post_build()

    def pre_build(self):
        main_layout = QtWidgets.QVBoxLayout()
        self.setLayout(main_layout)

    def build(self):
        self._tool_widget = QtWidgets.QWidget()
        _tool_widget_layout = QtWidgets.QVBoxLayout()
        self._tool_widget.setLayout(_tool_widget_layout)

        self.layout().addWidget(self._tool_widget)

    def post_build(self):
        '''Set up all the signals'''
        self._on_client_context_changed_callback()

    def _on_client_context_changed_callback(self, event=None):
        '''Client context has been changed'''
        super(BaseDialog, self)._on_client_context_changed_callback(event)
        # Clean the UI every time a new context is set as the current tool
        # config might not be available anymore
        self.clean_ui()
        self.pre_build_ui()
        self.build_ui()
        self.post_build_ui()

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

    def _on_run_button_clicked(self):
        raise NotImplementedError
