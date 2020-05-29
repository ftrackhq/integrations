
# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

from functools import partial

from Qt import QtWidgets


from ftrack_connect_pipeline_nuke import plugin
from ftrack_connect_pipeline_qt.client.widgets.options import BaseOptionsWidget

import nuke


class WriteNodesNukeWidget(BaseOptionsWidget):

    def __init__(
            self, parent=None, session=None, data=None, name=None,
            description=None, options=None, context=None
    ):

        self.write_nodes = nuke.allNodes('Write')

        super(WriteNodesNukeWidget, self).__init__(
            parent=parent,
            session=session, data=data, name=name,
            description=description, options=options,
            context=context
        )

    def build(self):
        super(WriteNodesNukeWidget, self).build()
        self.nodes_cb = QtWidgets.QComboBox()
        self.layout().addWidget(self.nodes_cb)
        node_names = [node.name() for node in self.write_nodes]
        if node_names:
            self.nodes_cb.addItems(node_names)
            update_fn = partial(self.set_option_result, key='node_name')
            self.nodes_cb.editTextChanged.connect(update_fn)
            self.set_option_result(node_names[0], 'node_name')
        else:
            self.nodes_cb.addItem('No Write Node found.')
            self.nodes_cb.setDisabled(True)


class WriteNodesPluginWidget(plugin.PublisherCollectorNukeWidget):
    plugin_name = 'write_node'
    widget = WriteNodesNukeWidget


def register(api_object, **kw):
    plugin = WriteNodesPluginWidget(api_object)
    plugin.register()
