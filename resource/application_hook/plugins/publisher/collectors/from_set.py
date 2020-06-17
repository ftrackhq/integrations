# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

import maya.cmds as cmd

from ftrack_connect_pipeline_maya import plugin
import ftrack_api


class CollectFromSetMayaPlugin(plugin.PublisherCollectorMayaPlugin):
    plugin_name = 'from_set'

    def run(self, context=None, data=None, options=None):

        set_name = options['set_name']
        return cmd.sets(set_name, q=True)


def register(api_object, **kw):
    if not isinstance(api_object, ftrack_api.Session):
        # Exit to avoid registering this plugin again.
        return
    plugin = CollectFromSetMayaPlugin(api_object)
    plugin.register()

