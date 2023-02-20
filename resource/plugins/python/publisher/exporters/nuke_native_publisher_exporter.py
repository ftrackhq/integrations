# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack

import ftrack_api

import tempfile

import nuke
import nukescripts

from ftrack_connect_pipeline_nuke import plugin


class NukeNativePublisherExporterPlugin(plugin.NukePublisherExporterPlugin):
    '''Nuke native script exporter plugin'''

    plugin_name = 'nuke_native_publisher_exporter'

    def run(self, context_data=None, data=None, options=None):
        '''Export collected Nuke script or nodes to a file based collected object in *data* and *options*'''

        new_file_path = tempfile.NamedTemporaryFile(
            delete=False, suffix='.nk'
        ).name

        collected_objects = []
        is_scene_publish = False
        for collector in data:
            collected_objects.extend(collector['result'])
            if collector.get('options', {}).get('export') == 'scene':
                is_scene_publish = True

        if is_scene_publish:
            self.logger.debug(
                'Publishing nuke scene to: "{}"'.format(new_file_path)
            )
            nuke.scriptSave(new_file_path)
        else:
            # Select the nodes to export
            nukescripts.clear_selection_recursive()
            for node_name in collected_objects:
                n = nuke.toNode(node_name)
                if n:
                    n.setSelected(True)
            self.logger.debug(
                'Saving selected nuke nodes to: "{}"'.format(new_file_path)
            )
            nuke.nodeCopy(new_file_path)

        return [new_file_path]


def register(api_object, **kw):
    if not isinstance(api_object, ftrack_api.Session):
        # Exit to avoid registering this plugin again.
        return
    plugin = NukeNativePublisherExporterPlugin(api_object)
    plugin.register()
