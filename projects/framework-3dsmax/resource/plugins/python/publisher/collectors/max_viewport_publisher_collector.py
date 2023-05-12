# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack

from pymxs import runtime as rt

from ftrack_connect_pipeline_3dsmax import plugin
import ftrack_api


class MaxViewportPublisherCollectorPlugin(plugin.MaxPublisherCollectorPlugin):
    plugin_name = 'max_viewport_publisher_collector'

    def fetch(self, context_data=None, data=None, options=None):
        '''Fetch all viewports in Max'''
        viewports = []
        for idx in range(1, (rt.viewport.numViewEx() + 1)):
            view_type = rt.viewport.getType(index=idx)
            entry = (str(view_type), idx)
            if str(view_type) == 'view_persp_user':  # USER_PERSP
                viewports.insert(0, entry)
            else:
                viewports.append(entry)
        return viewports

    def run(self, context_data=None, data=None, options=None):
        '''Return the viewport index from given *options*'''
        viewport_index = options.get('viewport_index', -1)
        if viewport_index != -1:
            return [viewport_index]
        return []


def register(api_object, **kw):
    if not isinstance(api_object, ftrack_api.Session):
        # Exit to avoid registering this plugin again.
        return
    plugin = MaxViewportPublisherCollectorPlugin(api_object)
    plugin.register()
