# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack

from pymxs import runtime as rt

import ftrack_api

from ftrack_connect_pipeline_3dsmax import plugin


class MaxGenericPublisherCollectorPlugin(plugin.MaxPublisherCollectorPlugin):
    plugin_name = 'max_generic_publisher_collector'

    def select(self, context_data=None, data=None, options=None):
        '''Select all the items of the plugin *options*'''
        selected_items = options.get('selected_items', [])
        rt.clearSelection()
        nodes_to_select = []
        for item in selected_items:
            if item:
                nodes_to_select.append(rt.getNodeByName(item))
        rt.select(nodes_to_select)
        return rt.selection

    def fetch(self, context_data=None, data=None, options=None):
        '''Fetch all selected items'''
        collected_objects = []
        for obj in rt.GetCurrentSelection():
            collected_objects.append(obj.name)
        return collected_objects

    def add(self, context_data=None, data=None, options=None):
        '''Return the selected items of the scene'''
        collected_objects = []
        for obj in rt.GetCurrentSelection():
            collected_objects.append(obj.name)
        return collected_objects

    def run(self, context_data=None, data=None, options=None):
        '''Return all the collected objects in the widget from the
        plugin *options*'''
        collected_objects = options.get('collected_objects', [])
        return collected_objects


def register(api_object, **kw):
    if not isinstance(api_object, ftrack_api.Session):
        # Exit to avoid registering this plugin again.
        return
    plugin = MaxGenericPublisherCollectorPlugin(api_object)
    plugin.register()
