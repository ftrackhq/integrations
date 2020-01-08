# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

import shutil
import tempfile
from ftrack_connect_pipeline import plugin


class PassthroughPlugin(plugin.OutputPlugin):
    plugin_name = 'passthrough'

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

        component_name = options['component_name']
        result = {}
        for item in data:
            result[component_name] = item

        return result


def register(api_object, **kw):
    plugin = PassthroughPlugin(api_object)
    plugin.register()