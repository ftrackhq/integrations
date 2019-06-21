# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

from ftrack_connect_pipeline import plugin


class NonEmptyValidatorPlugin(plugin.ValidatorPlugin):
    plugin_name = 'nonempty'

    def run(self, context=None, data=None, options=None):
        self.logger.info('data: {}'.format(data))
        return all(bool(datum) for datum in data)


def register(api_object, **kw):
    plugin = NonEmptyValidatorPlugin(api_object)
    plugin.register()
