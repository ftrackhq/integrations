# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack

from pymxs import runtime as rt

import ftrack_api

from ftrack_connect_pipeline_3dsmax import plugin


class MaxGeometryPublisherCollectorPlugin(plugin.MaxPublisherCollectorPlugin):
    plugin_name = 'max_geometry_publisher_collector'

    def select(self, context_data=None, data=None, options=None):
        '''Select all the items in the given plugin *options*'''
        selected_items = options.get('selected_items', [])
        rt.clearSelection()
        nodes_to_select = []
        for item in selected_items:
            if item:
                nodes_to_select.append(rt.getNodeByName(item))
        rt.select(nodes_to_select)
        return rt.selection

    def fetch(self, context_data=None, data=None, options=None):
        '''Fetch all selected geometries in the scene, if non selected return all'''
        collected_objects = []
        all_objects = rt.objects
        for obj in all_objects:
            if rt.superClassOf(obj) == rt.GeometryClass:
                collected_objects.append(obj.name)

        return collected_objects

    def add(self, context_data=None, data=None, options=None):
        '''Return the selected geometries'''
        selected_objects = rt.selection
        check_type = rt.GeometryClass
        collected_objects = []
        for obj in selected_objects:
            if rt.superClassOf(obj) == check_type:
                collected_objects.append(obj.name)
        return collected_objects

    def run(self, context_data=None, data=None, options=None):
        '''
        Return the collected objects in the widget from the plugin *options*
        '''
        geo_objects = options.get('collected_objects', [])
        return geo_objects


def register(api_object, **kw):
    if not isinstance(api_object, ftrack_api.Session):
        # Exit to avoid registering this plugin again.
        return
    plugin = MaxGeometryPublisherCollectorPlugin(api_object)
    plugin.register()
