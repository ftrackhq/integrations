# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

from ftrack_framework_plugin import BasePlugin


class ContextPlugin(BasePlugin):
    name = 'context'

    def run(self, store):
        '''
        Store values of the :obj:`self.options`
        'context_id ' in the
        given *store*
        '''
        keys = [
            'context_id',
        ]
        for k in keys:
            if self.options.get(k):
                store[k] = self.options.get(k)