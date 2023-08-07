# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

from ftrack_framework_plugin.base_finalizer_plugin import BaseFinalizerPlugin
from ftrack_framework_plugin import constants
from ftrack_framework_core import constants as core_constants

class GenericContextPassthroughPlugin(BaseFinalizerPlugin):
    name = 'generic_finalizer_publish_to_ftrack'
    host_type = constants.hosts.PYTHON_HOST_TYPE
    plugin_type = constants.PLUGIN_FINALIZER_TYPE
    '''Print given arguments'''

    def register_methods(self):
        self.register_method(
            method_name='run',
            required_output_type=dict,
            required_output_value=None
        )

    def run(self, context_data=None, data=None, options=None):
        self.logger.debug("given context_data: {}".format(context_data))
        self.logger.debug("given data: {}".format(data))
        self.logger.debug("given options: {}".format(options))
        # TODO: Make it easier to get the exporter result.
        # Return the exporter result
        publish_components = {}
        for step in self.plugin_data:
            if step['type'] == core_constants.COMPONENT:
                component_name = step['name']
                publish_components[component_name] =  []
                for stage in step['result']:
                    for plugin in stage['result']:
                        publish_components[component_name].append(plugin['plugin_method_result'])
        return publish_components
