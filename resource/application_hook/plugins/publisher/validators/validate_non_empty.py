# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

from ftrack_connect_pipeline import plugin


class NonEmptyValidatorPlugin(plugin.ValidatorPlugin):
    plugin_name = 'nonempty'

    def run(self, context=None, data=None, options=None):
        output = self.output
        self.logger.info('data: {}'.format(data))
        output = all(bool(datum) for datum in data)
        return output


def register(api_object, **kw):
    plugin = NonEmptyValidatorPlugin(api_object)
    plugin.register()
