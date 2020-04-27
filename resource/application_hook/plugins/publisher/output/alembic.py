# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

import tempfile

import MaxPlus
import pymxs

from ftrack_connect_pipeline_3dsmax import plugin


class OutputMaxAlembicPlugin(plugin.PublisherOutputMaxPlugin):
    plugin_name = 'OutputMaxAlembicPlugin'

    def run(self, context=None, data=None, options=None):
        component_name = options['component_name']
        new_file_path = tempfile.NamedTemporaryFile(
            delete=False, suffix='.abc'
        ).name
        self.logger.debug('Calling extractor options: data {}'.format(data))
        self.logger.debug('Writing Alembic file to {}'.format(new_file_path))
        # return {component_name: new_file_path}

        saved_selection = MaxPlus.SelectionManager.GetNodes()
        self.logger.debug('Post SM1')

        with pymxs.mxstoken():
            MaxPlus.SelectionManager.ClearNodeSelection()
            self.logger.debug('Post SM2')

            nodes = MaxPlus.INodeTab()
            for node_name in data:
                node = MaxPlus.INode.GetINodeByName(node_name)
                if node:
                    nodes.Append(node)
            MaxPlus.SelectionManager.SelectNodes(nodes)

            # pymxs.runtime.clearSelection()
            # for node_name in data:
            #     pymxs.runtime.selectMore(
            #         pymxs.runtime.getNodeByName(node_name)
            #     )
            pymxs.runtime.exportFile(
                new_file_path, pymxs.runtime.Name("noPrompt"), selectedOnly=True
            )
        return {component_name: new_file_path}


def register(api_object, **kw):
    plugin = OutputMaxAlembicPlugin(api_object)
    plugin.register()
