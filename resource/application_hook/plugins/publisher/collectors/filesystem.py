# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

import os
from ftrack_connect_pipeline import plugin


class FilesystemCollectPlugin(plugin.CollectorPlugin):
    plugin_name = 'filesystem'

    def run(self, context=None, data=None, options=None):
        '''*context* Dictionary with the asset_name, context_id, asset_type, comment and status_id of the asset that
        we are working on. Example: 'context': {u'asset_name': 'PipelineAsset',
                                                u'context_id': u'529af752-2274-11ea-a019-667d1218a15f',
                                                'asset_type': u'geo',
                                                 u'comment': 'A new hope',
                                                 u'status_id': u'44dd9fb2-4164-11df-9218-0019bb4983d8'}
        *data* list of data coming from previous collector or empty list
        *options* Dictionary of options added from the ui or manually added.
        Predefined available option: *option['path']*
        Return type: List
        Returns: List of paths of objects to collect '''
        return [options['path']]


def register(api_object, **kw):
    plugin = FilesystemCollectPlugin(api_object)
    plugin.register()