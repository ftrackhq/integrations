# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

from ftrack_connect_pipeline import plugin
import ftrack_api

class NumericValidatorPlugin(plugin.PublisherValidatorPlugin):
    plugin_name = 'numeric'

    def run(self, context=None, data=None, options=None):
        output = self.output
        self.logger.info('data: {}'.format(data))
        test = options.get('test')
        value = options.get('value')

        if len(data) != 1:
            output = False
            return output

        if test == '>=':
            output = int(data[0]) >= int(value)
            return output


def register(api_object, **kw):
    if not isinstance(api_object, ftrack_api.Session):
        # Exit to avoid registering this plugin again.
        return
    plugin = NumericValidatorPlugin(api_object)
    plugin.register()
