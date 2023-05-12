# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack
import tempfile

from pymxs import runtime as rt

import ftrack_api

from ftrack_connect_pipeline_3dsmax import plugin


class MaxFBXPublisherExporterPlugin(plugin.MaxPublisherExporterPlugin):
    plugin_name = 'max_fbx_publisher_exporter'

    extension = None
    file_type = None

    def run(self, context_data=None, data=None, options=None):
        '''Export Max objects to a temp file for publish'''

        new_file_path = tempfile.NamedTemporaryFile(
            delete=False, suffix='.fbx'
        ).name

        self.logger.debug('Calling extractor options: data {}'.format(data))
        self.logger.debug('Writing FBX file to {}'.format(new_file_path))

        saved_selection = rt.GetCurrentSelection()

        collected_objects = []
        for collector in data:
            collected_objects.extend(collector['result'])

        try:
            rt.clearSelection()

            nodes = []

            for node_name in collected_objects:
                node = rt.getNodeByName(node_name)
                if node:
                    nodes.append(node)
            rt.select(nodes)
            rt.exportFile(
                new_file_path,
                rt.Name("noPrompt"),
                selectedOnly=True,
                using=rt.FBXEXP,
            )
        finally:
            rt.select(saved_selection)

        return [new_file_path]


def register(api_object, **kw):
    if not isinstance(api_object, ftrack_api.Session):
        # Exit to avoid registering this plugin again.
        return
    output_plugin = MaxFBXPublisherExporterPlugin(api_object)
    output_plugin.register()
