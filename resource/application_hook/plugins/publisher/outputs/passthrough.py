# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

import shutil
import tempfile
from ftrack_connect_pipeline import plugin


class PassthroughPlugin(plugin.OutputPlugin):
    plugin_name = 'passthrough'

    def run(self, context=None, data=None, options=None):
        component_name = options['component_name']
        output = self.output
        for item in data:
            output[component_name] = item

        return output


def register(api_object, **kw):
    plugin = PassthroughPlugin(api_object)
    plugin.register()