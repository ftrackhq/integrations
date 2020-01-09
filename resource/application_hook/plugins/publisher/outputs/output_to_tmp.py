# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

import shutil
import tempfile
from ftrack_connect_pipeline import plugin


class TmpOutputPlugin(plugin.OutputPlugin):
    plugin_name = 'to_tmp'

    def run(self, context=None, data=None, options=None):
        output = self.output
        for item in data:
            new_file_path = tempfile.NamedTemporaryFile(delete=False).name
            shutil.copy(item, new_file_path)
            output[item] = new_file_path

        return output


def register(api_object, **kw):
    plugin = TmpOutputPlugin(api_object)
    plugin.register()