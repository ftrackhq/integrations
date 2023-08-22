# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

import shutil
import tempfile

from ftrack_framework_plugin import BasePlugin
import ftrack_constants.framework as constants


class CommonFilePublisherExporterPlugin(BasePlugin):
    '''Standalone publisher file exporter plugin'''

    name = 'common_file_publisher_exporter'
    host_type = constants.host.PYTHON_HOST_TYPE
    plugin_type = constants.plugin.PLUGIN_EXPORTER_TYPE

    def register_methods(self):
        self.register_method(
            method_name='run',
            required_output_type=list,
            required_output_value=None
        )

    def run(self, context_data=None, data=None, options=None):
        '''Copies the collected paths supplied by *data* to temp for publish'''
        output = []

        collected_objects = []
        for collector in data:
            collected_objects.extend(collector['result'])

        for item in collected_objects:
            new_file_path = tempfile.NamedTemporaryFile(delete=False).name
            shutil.copy(item, new_file_path)
            output.append(new_file_path)

        return output
