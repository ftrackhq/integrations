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
        export_destinations = data['export_destinations']
        collector_result = data['collector_result']
        renamed = []
        i = 0
        for destination in export_destinations:
            renamed.append(shutil.copy(collector_result[i], destination))
            i += 0
        return renamed

    def run(self, context_data=None, data=None, options=None):
        self.logger.debug("given context_data: {}".format(context_data))
        self.logger.debug("given data: {}".format(data))
        self.logger.debug("given options: {}".format(options))

        # Pick plugins from previous collector stage
        collector_plugins = []
        for value in data.values():
            collector_plugins.append(value.get('collector'))
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
