# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

import nuke

from ftrack_connect_pipeline_nuke import plugin


class OutputSequencePlugin(plugin.OutputNukePlugin):
    plugin_name = 'sequence'

    def run(self, context=None, data=None, options=None):
        node_name = data[0]
        node = nuke.toNode(node_name)
        file_path = node['file'].getValue()
        first, last = self.get_sequence_fist_last_frame(file_path)
        complete_sequence = '{} [{}-{}]'.format(file_path, first, last)

        component_name = options['component_name']
        return {component_name: complete_sequence}


def register(api_object, **kw):
    plugin = OutputSequencePlugin(api_object)
    plugin.register()
