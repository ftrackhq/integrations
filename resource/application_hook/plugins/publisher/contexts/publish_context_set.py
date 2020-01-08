# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

import os
from ftrack_connect_pipeline import plugin


class EnvContextPlugin(plugin.ContextPlugin):
    plugin_name = 'context.publish'

    def run(self, context=None, data=None, options=None):
        '''*context* Dictionary with the context information. Not used, should be None.
        *data* list of data coming from previous stage or empty list. Not used, should be Empty list
        or None.
        *options* Dictionary of options added from the ui or manually added. Check predefined available options on
        the publisher definition. Example Predefined available options: *context_id*, *asset_name*, *comment*,
        *status_id* .
        required options: *context_id* (defined on ContextPlugin class)
        Return type: Dictionary
        Returns: *context* Dictionary with the asset_name, context_id, asset_type, comment and status_id of the asset
        that we are working on. Example: 'context': {u'asset_name': 'PipelineAsset',
                                                    u'context_id': u'529af752-2274-11ea-a019-667d1218a15f',
                                                    'asset_type': u'geo',
                                                    u'comment': 'A new hope',
                                                    u'status_id': u'44dd9fb2-4164-11df-9218-0019bb4983d8'}
        Required return values in the dictionary: *context_id*, *asset_name*, *comment*, *status_id* '''

        return options


def register(api_object, **kw):
    plugin = EnvContextPlugin(api_object)
    plugin.register()