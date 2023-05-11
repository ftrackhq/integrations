# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack
import tempfile

from pymxs import mxstoken
from pymxs import runtime as rt

import ftrack_api

from ftrack_connect_pipeline_3dsmax import plugin


class MaxNativePublisherExporterPlugin(plugin.MaxPublisherExporterPlugin):
    plugin_name = 'max_native_publisher_exporter'

    extension = None
    file_type = None

    def run(self, context_data=None, data=None, options=None):
        '''Export Max objects to a temp file for publish'''

        self.extension = '.max'

        new_file_path = tempfile.NamedTemporaryFile(
            delete=False, suffix=self.extension
        ).name

        collected_objects = []
        is_scene_publish = False
        for collector in data:
            collected_objects.extend(collector['result'])
            if collector.get('options', {}).get('export') == 'scene':
                is_scene_publish = True

        if is_scene_publish:
            # Store current scene name
            scene_name = "{}{}".format(rt.maxFilePath, rt.maxFileName)

            # Save entire scene to temp
            rt.savemaxFile(new_file_path, useNewFile=False)

            if scene_name != '':
                # Save back to original location
                rt.savemaxFile(new_file_path, useNewFile=False)

        else:
            # Export a subset of the scene
            with mxstoken():
                rt.clearSelection()
            for node_name in collected_objects:
                node = rt.getNodeByName(node_name, exact=True)
                rt.selectMore(node)
            rt.saveNodes(rt.selection, new_file_path, quiet=True)

        return [new_file_path]


def register(api_object, **kw):
    if not isinstance(api_object, ftrack_api.Session):
        # Exit to avoid registering this plugin again.
        return
    output_plugin = MaxNativePublisherExporterPlugin(api_object)
    output_plugin.register()
