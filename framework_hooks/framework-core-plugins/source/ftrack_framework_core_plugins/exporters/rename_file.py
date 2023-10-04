# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

import shutil

from ftrack_framework_plugin import BasePlugin
import ftrack_constants.framework as constants


class RenameExporterPlugin(BasePlugin):
    name = 'rename_file_exporter'
    host_type = constants.host.PYTHON_HOST_TYPE
    plugin_type = constants.plugin.PLUGIN_EXPORTER_TYPE
    '''Rename the provided file'''

    def register_methods(self):
        self.register_method(
            method_name='run',
            required_output_type=list,
            required_output_value=None,
        )
        self.register_method(
            method_name='rename',
            required_output_type=None,
            required_output_value=None,
        )

    def rename(self, context_data=None, data=None, options=None):
        '''
        Expects export_destinations list and collector_result list in the given
        *data*. This method will rename the collector_result items to the
        export_tool_configs items.
        '''
        export_destinations = data['export_destinations']
        collector_result = data['collector_result']
        renamed = []
        i = 0
        for destination in export_destinations:
            renamed.append(shutil.copy(collector_result[i], destination))
            i += 0
        return renamed

    def run(self, context_data=None, data=None, options=None):
        '''
        Expects a dictionary with the previous collected data from the
        collector plugin in the given *data*. Also expects to have
        export_destinations list defined in the given *options*
        This method will return the result of the rename method.
        '''

        # Pick plugins from previous collector stage
        collector_plugins = []
        for key, value in data[self.plugin_step_name]['collector'].items():
            collector_plugins.append({key: value})
        # Pick result of collector plugins.
        collector_result = []
        for plugin in collector_plugins:
            collector_result.extend(list(plugin.values()))

        export_destinations = options['export_destinations']
        if type(export_destinations) == str:
            export_destinations = [export_destinations]

        return self.rename(
            data={
                'collector_result': collector_result,
                'export_destinations': export_destinations,
            }
        )
