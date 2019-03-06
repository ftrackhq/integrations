# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

import maya.cmds as cmd
import maya

from ftrack_connect_pipeline_maya import plugin


class CollectFromSetMayaPlugin(plugin.CollectorMayaPlugin):
    plugin_name = 'from_set'

    def run(self, context=None, data=None, options=None):

        def call(set_name):
            return cmd.sets(set_name, q=True)

        set_name = options['set_name']
        return maya.utils.executeInMainThreadWithResult(call, set_name)


def register(api_object, **kw):
    plugin = CollectFromSetMayaPlugin(api_object)
    plugin.register()

