# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

import os
from ftrack_connect_pipeline import plugin


class FilesystemCollectPlugin(plugin.CollectorPlugin):
    plugin_name = 'filesystem'

    def run(self, context=None, data=None, options=None):
        '''Run the current plugin with , *context* , *data* and *options*.

        *context* provides a mapping with the asset_name, context_id, asset_type,
        comment and status_id of the asset that we are working on.

        *data* a list of data coming from previous collector and
        *options* a dictionary of options passed from ourside.

        Returns a List of paths of objects to collect

        '''
        return [options['path']]


def register(api_object, **kw):
    plugin = FilesystemCollectPlugin(api_object)
    plugin.register()