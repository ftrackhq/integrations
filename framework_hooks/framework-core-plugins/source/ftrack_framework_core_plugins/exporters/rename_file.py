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
            required_output_type=str,
            required_output_value=None
        )

    def run(self, context_data=None, data=None, options=None):
        self.logger.debug("given context_data: {}".format(context_data))
        self.logger.debug("given data: {}".format(data))
        self.logger.debug("given options: {}".format(options))
        # TODO: Duplicate and rename provided file
        collector_result = data[0]['result'][0]['result'][0]['plugin_method_result']
        export_destination = options['export_destination']
        shutil.copy(collector_result, export_destination)
        return export_destination
