# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

import os
from ftrack_connect_pipeline import plugin


class EnvContextPlugin(plugin.ContextPlugin):
    plugin_name = 'context.publish'

    def run(self, context=None, data=None, options=None):

        return options


def register(api_object, **kw):
    plugin = EnvContextPlugin(api_object)
    plugin.register()