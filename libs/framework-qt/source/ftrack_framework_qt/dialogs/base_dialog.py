# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

try:
    from PySide6 import QtWidgets, QtCore
except ImportError:
    from PySide2 import QtWidgets, QtCore
from ftrack_framework_core.widget.dialog import FrameworkDialog

from ftrack_qt.widgets.dialogs import StyledDialog
from ftrack_qt.widgets.headers import SessionHeader
from ftrack_qt.utils.widget import (
    InputEventBlockingWidget,
)

from ftrack_qt.utils.layout import recursive_clear_layout


class BaseDialog(FrameworkDialog, StyledDialog):
    '''Default Framework dialog'''

    name = 'base_dialog'
    tool_config_type_filter = None
    run_button_title = 'run'
    ui_type = 'qt'

    @property
    def event_blocker_widget(self):
        return self._event_blocker_widget

    @property
    def stacked_widget(self):
        return self._stacked_widget

    @property
    def main_widget(self):
        return self._main_widget

    @property
    def overlay_widget(self):
        return self._overlay_widget

    @property
    def main_layout(self):
        return self._main_layout

    @property
    def overlay_layout(self):
        return self._overlay_layout

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
        return self.dialog_options.get('tool_configs')

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
        self._stacked_widget = None
        self._main_widget = None
        self._overlay_widget = None
        self._main_layout = None
        self._overlay_layout = None

        self._header = None
        self._tool_widget = None
        self._run_button = None

        self.pre_build()
        self.build()
        self.post_build()

    def pre_build(self):
        base_layout = QtWidgets.QVBoxLayout()

        self._stacked_widget = QtWidgets.QStackedWidget()
        self._main_widget = (
            QtWidgets.QWidget()
        )  # Main widget that holds the primary interface
        self._overlay_widget = (
            QtWidgets.QWidget()
        )  # Overlay widget that can cover the main interface

        self._main_layout = QtWidgets.QVBoxLayout()
        self._main_layout.setContentsMargins(0, 0, 0, 0)
        self._overlay_layout = QtWidgets.QVBoxLayout()
        self._overlay_layout.setContentsMargins(0, 0, 0, 0)

        self._main_widget.setLayout(self._main_layout)
        self._overlay_widget.setLayout(self._overlay_layout)

        # Add widgets to the stacked widget
        self._stacked_widget.addWidget(self._main_widget)
        self._stacked_widget.addWidget(self._overlay_widget)

        # Start event blocker
        # Adding the event blocker widget (even if lambda: False) to the layout prevents Maya 2022 from
        # crashing, specifically on Mac M1.
        self._event_blocker_widget = InputEventBlockingWidget(lambda: False)

        # Set the stacked widget as the central widget
        self.setLayout(base_layout)
        self.layout().addWidget(self._event_blocker_widget)
        self.layout().addWidget(self._stacked_widget)
        self.show_main_widget()

    def build(self):
        # Create the header
        self._header = SessionHeader(self.event_manager.session)

        self._tool_widget = QtWidgets.QWidget()
        _tool_widget_layout = QtWidgets.QVBoxLayout()
        self._tool_widget.setLayout(_tool_widget_layout)

        self._run_button = QtWidgets.QPushButton(self.run_button_title)

        self.main_layout.addWidget(self._header)
        self.main_layout.addWidget(self._tool_widget)
        self.main_layout.addWidget(self._run_button)

    def post_build(self):
        '''Set up all the signals'''
        self._on_client_context_changed_callback()
        # Connect run_tool_config button
        self._run_button.clicked.connect(self._on_run_button_clicked)

    def show_main_widget(self):
        '''Show the main widget'''
        self.show_widget(0)

    def show_overlay_widget(self):
        '''Show the overlay widget'''
        self.show_widget(1)

    def show_widget(self, idx):
        '''Show widget from stcked_widget with given *idx*'''
        if not self.stacked_widget.widget(idx):
            self.stacked_widget.setCurrentIndex(0)
            self.logger.warning(
                f"Given index {idx} doesn't exists, setting current widget to index 0"
            )
        self.stacked_widget.setCurrentIndex(idx)

    def add_stacked_widget(self, widget):
        '''Add given *widget to stack_widget'''
        self.stacked_widget.addWidget(widget)

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
        self.setWindowState(
            self.windowState() & ~QtCore.Qt.WindowState.WindowMinimized
            | QtCore.Qt.WindowState.WindowActive
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
        self._event_blocker_widget.stop()
        super(BaseDialog, self).closeEvent(event)
