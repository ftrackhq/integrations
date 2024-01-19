# :coding: utf-8
# :copyright: Copyright (c) 2014-2024 ftrack

import nuke

from ftrack_utils.paths import get_temp_path

from ftrack_framework_core.plugin import BasePlugin
from ftrack_framework_core.exceptions.plugin import PluginExecutionError


class NukeSaveToTempPlugin(BasePlugin):
    '''Save the current open Nuke script to a temp location'''

    name = 'nuke_save_to_temp_finalizer'

    def run(self, store):
        '''Save to temp and store the result in the given *store*'''
        temp_path = get_temp_path(filename_extension='.nk')

        self.logger.info(f'Saving Nuke script to temp: {temp_path}')
        try:
            save_result = nuke.scriptSaveAs(temp_path, overwrite=True)
        except Exception as e:
            self.logger.exception(e)
            raise PluginExecutionError(
                f'Exception saving Nuke script to temp: {e}'
            )
