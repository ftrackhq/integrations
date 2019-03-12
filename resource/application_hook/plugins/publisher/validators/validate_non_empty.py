# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

from ftrack_connect_pipeline import plugin


class NoneEmptyValidatorPlugin(plugin.ValidatorPlugin):
    plugin_name = 'nonempty'

    def run(self, context=None, data=None, options=None):
        return bool(data)


def register(api_object, **kw):
    plugin = NoneEmptyValidatorPlugin(api_object)
    plugin.register()
