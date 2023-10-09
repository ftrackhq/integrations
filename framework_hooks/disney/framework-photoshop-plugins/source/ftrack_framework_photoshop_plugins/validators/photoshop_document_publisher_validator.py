# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

from ftrack_framework_plugin import BasePlugin
import ftrack_constants.framework as constants


class PhotoshopDocumentPublisherValidatorPlugin(BasePlugin):
    '''Photoshop document publisher validator plugin'''

    name = 'photoshop_document_publisher_validator'
    host_type = constants.host.PYTHON_HOST_TYPE
    plugin_type = constants.plugin.PLUGIN_VALIDATOR_TYPE

    def register_methods(self):
        self.register_method(
            method_name='run',
            required_output_type=bool,
            required_output_value=True,
        )

    def validate(self, context_data=None, data=None, options=None):
        '''
        Expects a list of file paths in the given *data* dictionary in the
        collector_result key.
        '''
        collector_result = data['collector_result']
        if type(collector_result) == str:
            collector_result = [data['collector_result']]

        # Make sure exactly one document is collected
        output = len(collector_result) == 1 and all(
            bool(
                datum is not None
                and (len(datum) > 0 if hasattr(datum, '__len__') else True)
            )
            for datum in collector_result
        )

        if output:
            # TODO: Additional document validation can be performed here
            document_data = collector_result[0]

        return output

    def run(self, context_data=None, data=None, options=None):
        '''Validate that there are collected objects in *data* and they have a value'''

        collector_plugins = []
        for key, value in data[self.plugin_step_name]['collector'].items():
            collector_plugins.append({key: value})

        # Pick result of collector plugins.
        collector_result = []
        for plugin in collector_plugins:
            collector_result.extend(list(plugin.values()))

        return self.validate(data={'collector_result': collector_result})


