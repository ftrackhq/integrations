# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

from functools import partial

from ftrack_connect_pipeline.client.widgets import BaseWidget
from Qt import QtWidgets

from ftrack_connect_pipeline_3dsmax import plugin


class Camera3dsMaxWidget(BaseWidget):
    MAX_CAMERA_CLASS_ID = 32

    def __init__(self, session=None, data=None, name=None, description=None, options=None):
        import MaxPlus
        self.cameras = []
        root = MaxPlus.Core.GetRootNode()

        for node in root.Children:
            if node.Object.SuperClassID == self.MAX_CAMERA_CLASS_ID:
                self.cameras.append(node.name)

        super(Camera3dsMaxWidget, self).__init__(
            session=session, data=data, name=name, description=description,
            options=options
        )

    def build(self):
        super(Camera3dsMaxWidget, self).build()
        self.nodes_cb = QtWidgets.QComboBox()
        self.layout().addWidget(self.nodes_cb)
        camera_names = self.cameras
        if camera_names:
            self.nodes_cb.addItems(camera_names)
            update_fn = partial(self.set_option_result, key='camera_name')
            self.nodes_cb.editTextChanged.connect(update_fn)
            self.set_option_result(camera_names[0], 'camera_name')
        else:
            self.nodes_cb.addItem('No Camera found.')
            self.nodes_cb.setDisabled(True)


class Camera3dsMaxPlugin(plugin.CollectorMaxWidget):
    plugin_name = 'camera'

    def run(self, data=None, name=None, description=None, options=None):
        return Camera3dsMaxWidget(
            session=self.session, data=data, name=name,
            description=description, options=options
        )


def register(api_object, **kw):
    plugin = Camera3dsMaxPlugin(api_object)
    plugin.register()
