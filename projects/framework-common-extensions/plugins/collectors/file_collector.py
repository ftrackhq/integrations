# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

import os

from ftrack_constants import status as status_constants

from ftrack_framework_plugin import BasePlugin


class FileCollectorPlugin(BasePlugin):
    name = 'file_collector'

    def run(self, store):
        '''
        Get folder_path and file_name from the :obj:`self.options`
        and store the collected_file in the given *store*.
        '''
        folder_path = self.options.get('folder_path')
        file_name = self.options.get('file_name')
        if not folder_path or not file_name:
            self.status = status_constants.ERROR_STATUS
            self.message = (
                "Please provide folder_path and file_name in options. \n "
                "options: {}".format(self.options)
            )
            return
        component_name = self.options.get('component', 'main')
        store['components'][component_name]['collected_file'] = os.path.join(
            folder_path, file_name
        )
