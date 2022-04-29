# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack
import logging

from ftrack_connect_pipeline import utils
from ftrack_connect_pipeline_nuke.utils import custom_commands as nuke_utils


class QtSaveClient:
    '''Client for opening Connect documentation'''

    def __init__(self, event_manager, unused_asset_list_model):
        self.logger = logging.getLogger(
            __name__ + '.' + self.__class__.__name__
        )
        self._event_manager = event_manager

    def show(self):

        self.logger.info('Attempting to save local Nuke snapshot..')
        work_path, message = nuke_utils.save_snapshot(
            utils.ftrack_context_id(), self._event_manager.session
        )
        if not message is None:
            self.logger.info(message)
