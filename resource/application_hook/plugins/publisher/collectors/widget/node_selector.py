
# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

from functools import partial

from Qt import QtWidgets


from ftrack_connect_pipeline_nuke import plugin
from ftrack_connect_pipeline_qt.client.widgets.options import BaseOptionsWidget

import nuke


class NodeSelectorWidget(BaseOptionsWidget):

    def __init__(
            self, parent=None, session=None, data=None, name=None,
            description=None, options=None, context=None
    ):

        self.all_nodes = nuke.allNodes()
        if nuke.selectedNodes():
            self.last_selected_node = nuke.selectedNodes()[0]
        else:
            self.last_selected_node = None

        super(NodeSelectorWidget, self).__init__(
            parent=parent,
            session=session, data=data, name=name,
            description=description, options=options,
            context=context
        )

    def build(self):
        super(NodeSelectorWidget, self).build()
        self.nodes_cb = QtWidgets.QComboBox()
        self.nodes_cb.setToolTip(self.description)
        self.layout().addWidget(self.nodes_cb)
        node_names = [node.name() for node in self.all_nodes]
        if node_names:
            self.nodes_cb.addItems(node_names)
        else:
            self.nodes_cb.addItem('No nodes found.')
            self.nodes_cb.setDisabled(True)

    def post_build(self):
        super(NodeSelectorWidget, self).post_build()
        update_fn = partial(self.set_option_result, key='node_name')
        self.nodes_cb.editTextChanged.connect(update_fn)
        if self.last_selected_node:
            index = self.nodes_cb.findText(self.last_selected_node.name())
            self.nodes_cb.setCurrentIndex(index)
            self.set_option_result(self.last_selected_node.name(), 'node_name')
        else:
            self.set_option_result(self.nodes_cb.currentText(), 'node_name')


class NodeSelectorPluginWidget(plugin.PublisherCollectorNukeWidget):
    plugin_name = 'node_selector'
    widget = NodeSelectorWidget


def register(api_object, **kw):
    plugin = NodeSelectorPluginWidget(api_object)
    plugin.register()
