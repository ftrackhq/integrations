# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

from ftrack_connect_pipeline import plugin


class ValidatorLoaderTest(plugin.ValidatorPlugin):
    plugin_name = 'validatorTest'

    def run(self, context=None, data=None, options=None):
        return True


def register(api_object, **kw):
    plugin = ValidatorLoaderTest(api_object)
    plugin.register()
