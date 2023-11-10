# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

from ftrack_framework_plugin import BasePlugin


class StoreComponentPlugin(BasePlugin):
    name = 'store_component'

    def run(self, store):
        '''
        Store component value from :obj:`self.options` to components list of the
        given *store*.
        '''
        component_name = self.options.get('component')
        if component_name:
            store[component_name] = {}
            if not store.get('components'):
                store['components'] = []
            store['components'].append(component_name)
