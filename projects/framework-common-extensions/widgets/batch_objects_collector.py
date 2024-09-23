# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

try:
    from PySide6 import QtWidgets
except ImportError:
    from PySide2 import QtWidgets

from ftrack_framework_qt.widgets import BaseWidget
from ftrack_qt.widgets.selectors import OpenAssetSelector
from ftrack_qt.utils.decorators import invoke_in_qt_main_thread


class BatchObjectsCollectorWidget(BaseWidget):
    '''Main class to represent an asset version selector widget.'''

    name = "batch_objects_collector"
    ui_type = "qt"

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
        '''Initialize PublishContextWidget with *parent*, *session*, *data*,
        *name*, *description*, *options* and *context*
        '''
        self._title_label = None
        self._object_list = None
        self._collect_button = None

        super(BatchObjectsCollectorWidget, self).__init__(
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
        '''Set up the main layout for the widget.'''
        main_layout = QtWidgets.QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(main_layout)

    def build_ui(self):
        '''Build the user interface for the widget.'''
        self._title_label = QtWidgets.QLabel('Collected objects')

        self._object_list = QtWidgets.QListWidget()

        self.layout().addWidget(self._title_label)
        self.layout().addWidget(self._object_list)

    def post_build_ui(self):
        '''Perform post-construction operations.'''
        pass

    def populate(self):
        '''Fetch info from plugin to populate the widget'''
        self.query_assets()

    def query_assets(self):
        '''Query assets based on the context and asset type.'''
        payload = {
            'source_folder': self.plugin_config.get('options', {}).get(
                'source_folder'
            ),
        }
        self.run_ui_hook(payload)

    @invoke_in_qt_main_thread
    def ui_hook_callback(self, ui_hook_result):
        '''Handle the result of the UI hook.'''
        super(BatchObjectsCollectorWidget, self).ui_hook_callback(
            ui_hook_result
        )
        for object in ui_hook_result:
            self._object_list.addItem(object['obj_name'])
        self.set_plugin_option('collected_objects', ui_hook_result)
