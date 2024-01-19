# :coding: utf-8
# :copyright: Copyright (c) 2014-2024 ftrack
import tempfile

import nuke

from ftrack_framework_core.plugin import BasePlugin
from ftrack_framework_core.exceptions.plugin import PluginExecutionError


class NukeSaveToTemp(BasePlugin):
    '''Save the current open Nuke script to a temp location'''

    name = 'nuke_save_to_temp'

    def run(self, store):
        temp_path = tempfile.NamedTemporaryFile(
            delete=False, suffix='.nk'
        ).name

        self.logger.info(f'Saving Nuke script to temp: {temp_path}')
        try:
            save_result = nuke.scriptSaveAs(temp_path, overwrite=True)
        except Exception as e:
            self.logger.exception(e)
            raise PluginExecutionError(
                f'Exception saving Nuke script to temp: {e}'
            )

        store['save_to_temp_result'] = save_result
