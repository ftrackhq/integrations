# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack
import os.path

try:
    from PySide6 import QtWidgets, QtCore
except ImportError:
    from PySide2 import QtWidgets, QtCore

from ftrack_framework_qt.widgets import BaseWidget
from ftrack_qt.utils.decorators import invoke_in_qt_main_thread


class GenericObjectCollectorWidget(BaseWidget):
    '''Main class to represent a context widget on a publish process.'''

    name = 'generic_object_collector'
    ui_type = 'qt'

    items_changed = QtCore.Signal(object)

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
        '''initialise PublishContextWidget with *parent*, *session*, *data*,
        *name*, *description*, *options* and *context*
        '''
        self._object_list = None
        self._add_button = None
        self._remove_button = None

        super(GenericObjectCollectorWidget, self).__init__(
            event_manager,
            client_id,
            context_id,
            plugin_config,
            group_config,
            on_set_plugin_option,
            on_run_ui_hook,
            parent,
        )

    def pre_build_ui(self):
        layout = QtWidgets.QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setAlignment(QtCore.Qt.AlignTop)
        self.setLayout(layout)
        self.setSizePolicy(
            QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Fixed
        )

    def build_ui(self):
        '''build function widgets.'''

        self._object_list = QtWidgets.QListWidget()

        buttons_layout = QtWidgets.QHBoxLayout()
        self._add_button = QtWidgets.QPushButton('Add')
        self._remove_button = QtWidgets.QPushButton('Remove')

        self.layout().addWidget(self._object_list)
        buttons_layout.addWidget(self._add_button)
        buttons_layout.addWidget(self._remove_button)
        self.layout().addLayout(buttons_layout)

    def post_build_ui(self):
        '''hook events'''
        self._add_button.clicked.connect(self._on_add_object_callback)
        self._remove_button.clicked.connect(self._on_remove_object_callback)

    def _on_add_object_callback(self):
        # TODO: query object from scene and add the result into the list
        self._query_selected_objects()

    def _on_remove_object_callback(self):
        selected_items = self._object_list.selectedItems()
        for item in selected_items:
            self._object_list.takeItem(self._object_list.row(item))
        self.items_changed.emit(self._object_list.items())

    def _query_selected_objects(self):
        payload = {}
        self.run_ui_hook(payload)

    @invoke_in_qt_main_thread
    def ui_hook_callback(self, ui_hook_result):
        '''Handle the result of the UI hook.'''
        super(GenericObjectCollectorWidget, self).ui_hook_callback(
            ui_hook_result
        )
        self._object_list.addItems(ui_hook_result)
        self.items_changed.emit(self._object_list.items())
