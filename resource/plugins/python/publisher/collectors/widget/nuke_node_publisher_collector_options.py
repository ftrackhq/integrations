# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack

import ftrack_api

from functools import partial

from ftrack_connect_pipeline_nuke import plugin
from ftrack_connect_pipeline_qt.plugin.widget import BaseOptionsWidget

from Qt import QtWidgets


class NukeNodePublisherCollectorOptionsWidget(BaseOptionsWidget):
    '''Nuke single node user selection plugin widget'''

    # Run fetch function on widget initialization
    auto_fetch_on_init = True

    def __init__(
        self,
        parent=None,
        session=None,
        data=None,
        name=None,
        description=None,
        options=None,
        context_id=None,
        asset_type_name=None,
    ):

        self.node_names = []

        super(NukeNodePublisherCollectorOptionsWidget, self).__init__(
            parent=parent,
            session=session,
            data=data,
            name=name,
            description=description,
            options=options,
            context_id=context_id,
            asset_type_name=asset_type_name,
        )

    def on_fetch_callback(self, result):
        '''This function is called by the _set_internal_run_result function of
        the BaseOptionsWidget'''
        self.node_names = result
        if self.node_names:
            self.nodes_cb.setDisabled(False)
        else:
            self.nodes_cb.setDisabled(True)
        self.nodes_cb.clear()
        self.nodes_cb.addItems(self.node_names)

    def build(self):
        super(NukeNodePublisherCollectorOptionsWidget, self).build()
        self.nodes_cb = QtWidgets.QComboBox()
        self.layout().addWidget(self.nodes_cb)

        if self.options.get('node_name'):
            self.node_names.append(self.options.get('node_name'))

        if not self.node_names:
            self.nodes_cb.addItem('No Node found.')
            self.nodes_cb.setDisabled(True)
        else:
            self.nodes_cb.addItems(self.node_names)
        self.report_input()

    def _on_node_selected(self, node_name):
        if len(node_name) > 0:
            self.set_option_result(node_name, 'node_name')
        elif 'node_name' in self.options:
            del self.options['node_name']

    def post_build(self):
        super(NukeNodePublisherCollectorOptionsWidget, self).post_build()

        self.nodes_cb.currentTextChanged.connect(self._on_node_selected)
        if self.node_names:
            self._on_node_selected(self.nodes_cb.currentText())

    def report_input(self):
        '''(Override) Amount of collected objects has changed, notify parent(s)'''
        message = ''
        status = False
        num_objects = 1 if len(self.options.get('node_name') or '') > 0 else 0
        if num_objects > 0:
            message = '{} node{} selected'.format(
                num_objects, 's' if num_objects > 1 else ''
            )
            status = True
        self.inputChanged.emit(
            {
                'status': status,
                'message': message,
            }
        )


class NukeNodePublisherCollectorPluginWidget(
    plugin.NukePublisherCollectorPluginWidget
):
    plugin_name = 'nuke_node_publisher_collector'
    widget = NukeNodePublisherCollectorOptionsWidget


def register(api_object, **kw):
    if not isinstance(api_object, ftrack_api.Session):
        # Exit to avoid registering this plugin again.
        return
    plugin = NukeNodePublisherCollectorPluginWidget(api_object)
    plugin.register()
