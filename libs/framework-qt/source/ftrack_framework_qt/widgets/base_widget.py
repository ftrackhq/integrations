# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

try:
    from PySide6 import QtWidgets, QtCore
except ImportError:
    from PySide2 import QtWidgets, QtCore, QtGui

from ftrack_framework_core.widget.widget import FrameworkWidget


class BaseWidget(FrameworkWidget, QtWidgets.QWidget):
    '''Main class to represent base framework widget.'''

    name = 'base_widget'
    ui_type = 'qt'

    def __init__(
        self,
        event_manager,
        client_id,
        context_id,
        plugin_config,
        group_config,
        on_set_plugin_option,
        on_run_ui_hook,
        parent=None,
    ):
        '''initialise base widget with *parent*, *session*, *data*,
        *name*, *description*, *options* and *context*
        '''

        QtWidgets.QWidget.__init__(self, parent=parent)
        FrameworkWidget.__init__(
            self,
            event_manager,
            client_id,
            context_id,
            plugin_config,
            group_config,
            on_set_plugin_option,
            on_run_ui_hook,
            parent=parent,
        )

        self.pre_build_ui()
        self.build_ui()
        self.post_build_ui()
