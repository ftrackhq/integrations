# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack
import os
from ftrack_connect_pipeline import plugin


class FileExistsValidatorPlugin(plugin.ValidatorPlugin):
    plugin_name = 'file_exists'

    def run(self, context=None, data=None, options=None):
        result = all(bool(os.path.exists(datum)) for datum in data)
        self.logger('result  : {}'.format(result))


def register(api_object, **kw):
    plugin = FileExistsValidatorPlugin(api_object)
    plugin.register()
