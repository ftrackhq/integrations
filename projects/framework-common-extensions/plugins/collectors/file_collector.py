# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

import os

from ftrack_framework_plugin import BasePlugin
import ftrack_constants.framework as constants


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
            self.status = constants.status.ERROR_STATUS
            self.message = (
                "Please provide folder_path and file_name in options. \n "
                "options: {}".format(self.options)
            )
            return
        component_name = self.options.get('component', 'main')
        store['components'][component_name]['collected_file'] = os.path.join(
            folder_path, file_name
        )
