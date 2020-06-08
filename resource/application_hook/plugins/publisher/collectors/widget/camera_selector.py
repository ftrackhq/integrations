# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

from functools import partial

from ftrack_connect_pipeline_3dsmax import plugin
from ftrack_connect_pipeline_qt.client.widgets.options import BaseOptionsWidget

from Qt import QtWidgets

import MaxPlus


class Camera3dsMaxWidget(BaseOptionsWidget):
    MAX_CAMERA_CLASS_ID = 32

    def __init__(
            self, parent=None, session=None, data=None, name=None,
            description=None, options=None, context=None
    ):
        self.cameras = []
        root = MaxPlus.Core.GetRootNode()

        for node in root.Children:
            if node.Object.SuperClassID == self.MAX_CAMERA_CLASS_ID:
                self.cameras.append(node.name)

        super(Camera3dsMaxWidget, self).__init__(
            parent=parent, session=session, data=data, name=name,
            description=description, options=options, context=context
        )

    def build(self):
        super(Camera3dsMaxWidget, self).build()
        self.nodes_cb = QtWidgets.QComboBox()
        self.layout().addWidget(self.nodes_cb)

    def post_build(self):
        super(Camera3dsMaxWidget, self).post_build()
        camera_names = self.cameras
        if camera_names:
            self.nodes_cb.addItems(camera_names)
            update_fn = partial(self.set_option_result, key='camera_name')
            self.nodes_cb.editTextChanged.connect(update_fn)
            self.set_option_result(camera_names[0], 'camera_name')
        else:
            self.nodes_cb.addItem('No Camera found.')
            self.nodes_cb.setDisabled(True)


class Camera3dsMaxPluginWidget(plugin.PublisherCollectorMaxWidget):
    plugin_name = 'camera'
    widget = Camera3dsMaxWidget

def register(api_object, **kw):
    plugin = Camera3dsMaxPluginWidget(api_object)
    plugin.register()
