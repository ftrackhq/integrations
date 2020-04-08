# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

from ftrack_connect_pipeline import plugin

class FinaliserLoaderTest(plugin.LoaderFinaliserPlugin):
    plugin_name = 'finaliserTest'

    def run(self, context=None, data=None, options=None):
        return {}


def register(api_object, **kw):
    plugin = FinaliserLoaderTest(api_object)
    plugin.register()
