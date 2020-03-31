# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

import os
from ftrack_connect_pipeline import plugin


class CollectorLoaderTest(plugin.CollectorPlugin):
    plugin_name = 'collectorTest'

    def run(self, context=None, data=None, options=None):
        return []


def register(api_object, **kw):
    plugin = CollectorLoaderTest(api_object)
    plugin.register()