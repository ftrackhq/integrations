# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

import shutil
import tempfile
from ftrack_connect_pipeline import plugin


class TmpOutputPlugin(plugin.OutputPlugin):
    plugin_name = 'to_tmp'

    def run(self, context=None, data=None, options=None):
        '''*context* Dictionary with the asset_name, context_id, asset_type, comment and status_id of the asset that
        we are working on. Example: 'context': {u'asset_name': 'PipelineAsset',
                                                u'context_id': u'529af752-2274-11ea-a019-667d1218a15f',
                                                'asset_type': u'geo',
                                                 u'comment': 'A new hope',
                                                 u'status_id': u'44dd9fb2-4164-11df-9218-0019bb4983d8'}
        *data* list of data coming from collectors with path of the collected objects
        *options* Dictionary of options added from the ui or manually added.
        Required options: *component_name* (Automatically added on run_component function of BaseEngine Class)
        Return type: dictionary
        Returns: Dictionary with new data. Example {'main':'/path/to/asset.txt'} '''
        result = {}
        for item in data:
            new_file_path = tempfile.NamedTemporaryFile(delete=False).name
            shutil.copy(item, new_file_path)
            result[item] = new_file_path

        return result


def register(api_object, **kw):
    plugin = TmpOutputPlugin(api_object)
    plugin.register()