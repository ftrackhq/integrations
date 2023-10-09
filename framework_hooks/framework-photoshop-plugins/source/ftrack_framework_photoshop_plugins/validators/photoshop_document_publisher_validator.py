# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

from ftrack_framework_plugin import BasePlugin
import ftrack_constants.framework as constants


class PhotoshopDocumentPublisherValidatorPlugin(BasePlugin):
    '''Photoshop document publisher validator plugin'''

    name = 'photoshop_document_publisher_validator'
    host_type = 'photoshop'
    plugin_type = constants.plugin.PLUGIN_VALIDATOR_TYPE

    def register_methods(self):
        self.register_method(
            method_name='run',
            required_output_type=bool,
            required_output_value=True,
        )

    def run(self, context_data=None, data=None, options=None):
        '''Validate that there are collected objects in *data* and they have a value'''

        collected_objects = []
        for collector_result in list(
            data[self.plugin_step_name]['collector'].values()
        ):
            collected_objects.extend(collector_result)

        # Make sure exactly one document is collected
        output = len(collected_objects) == 1 and all(
            bool(
                datum is not None
                and (len(datum) > 0 if hasattr(datum, '__len__') else True)
            )
            for datum in collected_objects
        )

        if output:
            # TODO: Additional document validation can be performed here
            document_data = collected_objects[0]

        return output
