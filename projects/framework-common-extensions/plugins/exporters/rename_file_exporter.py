# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack
import os.path
import shutil

from ftrack_framework_core.plugin import BasePlugin


class RenameExporterPlugin(BasePlugin):
    name = 'rename_file_exporter'

    def rename(self, origin_path, destination_path):
        '''
        Rename the given *origin_path* to *destination_path*
        '''
        return shutil.copy(origin_path, os.path.expanduser(destination_path))

    def run(self, store):
        '''
        Expects collected_path in the <component_name> key of the given *store*
        and an export_destination from the :obj:`self.options`.
        '''
        component_name = self.options.get('component')

        collected_path = store['components'][component_name]['collected_path']
        export_destination = self.options['export_destination']

        store['components'][component_name]['exported_path'] = self.rename(
            collected_path, export_destination
        )
