# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

from ftrack_framework_plugin import BasePlugin


class AssetContextPlugin(BasePlugin):
    name = 'asset_context'

    def run(self, store):
        '''
        Store values of the :obj:`self.options`
        'context_id', 'asset_name', 'comment', 'status_id' keys in the
        given *store*
        '''
        # TODO: shouldn't asset_id and asset_type_name be here as well?
        keys = ['context_id', 'asset_name', 'comment', 'status_id']
        for k in keys:
            if self.options.get(k):
                store[k] = self.options.get(k)
