# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

from ftrack_framework_plugin import BasePlugin
import ftrack_constants.framework as constants


class CommonNonEmptyPublisherValidatorPlugin(BasePlugin):
    '''Publisher non empty validator plugin'''

    name = 'common_non_empty_publisher_validator'
    host_type = constants.host.PYTHON_HOST_TYPE
    plugin_type = constants.plugin.PLUGIN_VALIDATOR_TYPE

    def register_methods(self):
        self.register_method(
            method_name='run',
            required_output_type=list,
            required_output_value=True,
        )

    def run(self, context_data=None, data=None, options=None):
        '''Validate that there are collected objects in *data* and they have a value'''

        collected_objects = []
        for collector in data:
            collected_objects.extend(collector['result'])
        output = len(collected_objects) > 0 and all(
            bool(
                datum is not None
                and (len(datum) > 0 if hasattr(datum, '__len__') else True)
            )
            for datum in collected_objects
        )
        if output is True and 'amount' in options:
            amount = options['amount']
            output = len(collected_objects) == amount
        return output
