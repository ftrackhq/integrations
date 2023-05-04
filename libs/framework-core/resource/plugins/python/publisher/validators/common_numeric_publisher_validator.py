# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack

from ftrack_connect_pipeline import plugin
import ftrack_api


class CommonNumericPublisherValidatorPlugin(plugin.PublisherValidatorPlugin):
    '''Publisher numeric validator plugin'''

    plugin_name = 'common_numeric_publisher_validator'

    def run(self, context_data=None, data=None, options=None):
        '''Do a numerical validation on *data* based on *options*'''

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
    plugin = CommonNumericPublisherValidatorPlugin(api_object)
    plugin.register()
