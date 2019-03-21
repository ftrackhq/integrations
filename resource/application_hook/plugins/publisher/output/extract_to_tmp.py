# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

import shutil
import tempfile
from ftrack_connect_pipeline import plugin


class TmpExtractorPlugin(plugin.ExtractorPlugin):
    plugin_name = 'to_tmp'

    def run(self, context=None, data=None, options=None):
        result = {}
        for item in data:
            new_file_path = tempfile.NamedTemporaryFile(delete=False).name
            shutil.copy(item, new_file_path)
            result[item] = new_file_path

        return result


def register(api_object, **kw):
    plugin = TmpExtractorPlugin(api_object)
    plugin.register()