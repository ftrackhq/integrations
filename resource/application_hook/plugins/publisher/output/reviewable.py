# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

import tempfile

import maya.cmds as cmd
import maya

from ftrack_connect_pipeline_maya import plugin


class ExtractMayaAsciiPlugin(plugin.ExtractorMayaPlugin):
    plugin_name = 'thumbnail'

    def run(self, context=None, data=None, options=None):
        pass


def register(api_object, **kw):
    plugin = ExtractMayaAsciiPlugin(api_object)
    plugin.register()
