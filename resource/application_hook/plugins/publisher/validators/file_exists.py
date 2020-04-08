# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

import os
from ftrack_connect_pipeline import plugin

class FileExistsValidatorPlugin(plugin.PublisherValidatorPlugin):
    plugin_name = 'file_exists'

    def run(self, context=None, data=None, options=None):
        output = self.output
        output = all(bool(os.path.exists(datum)) for datum in data)
        return output


def register(api_object, **kw):
    plugin = FileExistsValidatorPlugin(api_object)
    plugin.register()
