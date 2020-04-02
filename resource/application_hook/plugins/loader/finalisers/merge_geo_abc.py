# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

import maya.cmds as cmd

from ftrack_connect_pipeline_maya import plugin


class MergeGeoAbcMayaPlugin(plugin.FinaliserMayaPlugin):
    plugin_name = 'merge_geo_abc'

    def run(self, context=None, data=None, options=None):
        return {}


def register(api_object, **kw):
    plugin = MergeGeoAbcMayaPlugin(api_object)
    plugin.register()