# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

from ftrack_framework_plugin import BasePlugin


# TODO: Rename this plugin and also do some checks like check that all the keys are in options
class GenericContextPassthroughPlugin(BasePlugin):
    name = 'generic_context_passthrough'

    def run(self, store):
        '''
        Update the required output value with the values of the given *options*
        '''
        keys = ['context_id', 'asset_name', 'comment', 'status_id']
        for k in keys:
            store[k] = self.options.get(k)
