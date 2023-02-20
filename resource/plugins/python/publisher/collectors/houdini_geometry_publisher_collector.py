# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack

import hou

from ftrack_connect_pipeline_houdini import plugin
import ftrack_api


class HoudiniGeometryPublisherCollectorPlugin(
    plugin.HoudiniPublisherCollectorPlugin
):
    plugin_name = 'houdini_geometry_publisher_collector'

    def select(self, context_data=None, data=None, options=None):
        '''Select all the items in the given plugin *options*'''
        selected_items = options.get('selected_items', [])
        for obj in hou.node('/').allSubChildren():
            obj.setSelected(
                1, obj in selected_items or obj.path() in selected_items
            )
        return selected_items

    def fetch(self, context_data=None, data=None, options=None):
        '''Fetch all selected geometries in the scene, if non selected return all'''
        selected_objects = hou.selectedNodes()
        if selected_objects:
            objPath = hou.node('/obj')
            geometry_objects = objPath.glob('*')
            collected_objects = []
            for obj in selected_objects:
                if obj in geometry_objects:
                    collected_objects.append(obj.path())
            return collected_objects
        else:
            collected_objects = hou.node('/obj').allSubChildren()
            return [obj.path() for obj in collected_objects]

    def add(self, context_data=None, data=None, options=None):
        '''Return the selected geometries'''
        selected_objects = hou.selectedNodes()
        objPath = hou.node('/obj')
        geometry_objects = objPath.glob('*')
        collected_objects = []
        for obj in selected_objects:
            if obj in geometry_objects:
                collected_objects.append(obj.path())
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
    plugin = HoudiniGeometryPublisherCollectorPlugin(api_object)
    plugin.register()
