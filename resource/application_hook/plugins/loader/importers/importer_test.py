# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

from ftrack_connect_pipeline import plugin


class ImporterLoaderTest(plugin.ImporterPlugin):
    plugin_name = 'importerTest'

    def run(self, context=None, data=None, options=None):
        print "data ---> {}".format(data)
        print "options ---> {}".format(options)
        return {}


def register(api_object, **kw):
    plugin = ImporterLoaderTest(api_object)
    plugin.register()
