# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

import tempfile

import pymxs

from ftrack_connect_pipeline_3dsmax import plugin


class ExtractMaxAlembicPlugin(plugin.ExtractorMaxPlugin):
    plugin_name = 'ExtractMaxAlembicPlugin'

    def run(self, context=None, data=None, options=None):
        component_name = options['component_name']
        new_file_path = tempfile.NamedTemporaryFile(
            delete=False, suffix='.abc'
        ).name
        self.logger.debug('Calling extractor options: data {}'.format(data))

        with pymxs.mxstoken():
            pymxs.runtime.clearSelection()
            for node_name in data:
                pymxs.runtime.selectMore(
                    pymxs.runtime.getNodeByName(node_name)
                )
            pymxs.runtime.exportFile(new_file_path, pymxs.runtime.Name("noPrompt"))
        return {component_name: new_file_path}


def register(api_object, **kw):
    plugin = ExtractMaxAlembicPlugin(api_object)
    plugin.register()
