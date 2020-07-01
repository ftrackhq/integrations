# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack

import ftrack_api

import tempfile
import nuke

from ftrack_connect_pipeline_nuke import plugin


class OutputNukeScriptPlugin(plugin.PublisherOutputNukePlugin):
    plugin_name = 'nukescript'

    def run(self, context=None, data=None, options=None):
        component_name = options['component_name']

        new_file_path = tempfile.NamedTemporaryFile(delete=False, suffix='.nk').name
        self.logger.debug('Calling extractor options: data {}'.format(data))
        nuke.scriptSave(new_file_path)

        return {component_name: new_file_path}


def register(api_object, **kw):
    if not isinstance(api_object, ftrack_api.Session):
        # Exit to avoid registering this plugin again.
        return
    plugin = OutputNukeScriptPlugin(api_object)
    plugin.register()
