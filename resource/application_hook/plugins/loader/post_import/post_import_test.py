# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

from ftrack_connect_pipeline import plugin

class PostImportLoaderTest(plugin.LoaderPostImportPlugin):
    plugin_name = 'postImportTest'

    def run(self, context=None, data=None, options=None):
        return {}


def register(api_object, **kw):
    plugin = PostImportLoaderTest(api_object)
    plugin.register()
