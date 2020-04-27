# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

import tempfile

import MaxPlus
import pymxs

from ftrack_connect_pipeline_3dsmax import plugin


class OutputMaxBinaryPlugin(plugin.PublisherOutputMaxPlugin):
    plugin_name = 'OutputMaxBinaryPlugin'

    def run(self, context=None, data=None, options=None):
        component_name = options['component_name']
        new_file_path = tempfile.NamedTemporaryFile(
            delete=False, suffix='.max'
        ).name
        self.logger.debug('Calling extractor options: data {}'.format(data))
        self.logger.debug('Writing Max file to {}'.format(new_file_path))
        # nodes = MaxPlus.INodeTab()
        with pymxs.mxstoken():
            # MaxPlus.Core.EvalMAXScript('clearSelection()')
            pymxs.runtime.execute('clearSelection()')
        self.logger.debug('maxbin 1')
        for node_name in data:
            self.logger.debug('maxbin 2')
            MaxPlus.Core.EvalMAXScript('selectMore ${}'.format(node_name))
            # node = MaxPlus.INode.GetINodeByName(node_name)
            # if node:
            #     nodes.Append(node)
        self.logger.debug('maxbin 3')
        # MaxPlus.FileManager.SaveNodes(nodes, new_file_path, quiet=True)
        MaxPlus.FileManager.SaveSelected(temporary_path)
        return {component_name: new_file_path}


def register(api_object, **kw):
    plugin = OutputMaxBinaryPlugin(api_object)
    plugin.register()
