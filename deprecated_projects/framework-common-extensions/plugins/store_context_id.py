# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

from ftrack_framework_core.plugin import BasePlugin


class ContextIdPlugin(BasePlugin):
    name = 'store_context_id'

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
                self.logger.debug(f"{store[k]} stored in {k}.")
