# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

try:
    from PySide6 import QtWidgets, QtCore
except ImportError:
    from PySide2 import QtWidgets, QtCore

from ftrack_framework_qt.widgets import BaseWidget
from ftrack_qt.utils.decorators import invoke_in_qt_main_thread


class BlenderCameraSelectorWidget(BaseWidget):
    '''Drop-down list to select the desired camera.'''

    name = 'blender_camera_selector'
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
        self._camera_cb = None

        super(BlenderCameraSelectorWidget, self).__init__(
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
        # Create export type combo box
        self._camera_cb = QtWidgets.QComboBox()
        self.layout().addWidget(self._camera_cb)

    def post_build_ui(self):
        '''hook events'''
        self._camera_cb.currentTextChanged.connect(self._on_camera_changed)

    def populate(self):
        '''Fetch info from plugin to populate the widget'''
        self.query_cameras()

    def query_cameras(self):
        '''Query All cameras from scene.'''
        payload = {}
        self.run_ui_hook(payload)

    @invoke_in_qt_main_thread
    def ui_hook_callback(self, ui_hook_result):
        '''Handle the result of the UI hook.'''
        super(BlenderCameraSelectorWidget, self).ui_hook_callback(ui_hook_result)
        self._camera_cb.addItems(ui_hook_result)
        default_camera_name = self.plugin_config['options'].get(
            'camera_name', 'Camera'
        )
        self._camera_cb.setCurrentText(default_camera_name)

    def _on_camera_changed(self, camera_name):
        '''Updates the camera_name option with the provided *camera_name'''
        if not camera_name:
            return
        self.set_plugin_option('camera_name', camera_name)
