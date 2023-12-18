# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

import shutil

from ftrack_framework_core.plugin import BasePlugin


class RenameExporterPlugin(BasePlugin):
    name = 'rename_file_exporter'

    def rename(self, origin_file, destination_file):
        '''
        Rename the given *origin_file to *destination_file*
        '''
        return shutil.copy(origin_file, destination_file)

    def run(self, store):
        '''
        Expects collected_file in the <component_name> key of the given *store*
        and an export_destination from the :obj:`self.options`.
        '''
        component_name = self.options.get('component')

        collected_file = store['components'][component_name]['collected_file']
        export_destination = self.options['export_destination']

        store['components'][component_name]['exported_path'] = self.rename(
            collected_file, export_destination
        )
