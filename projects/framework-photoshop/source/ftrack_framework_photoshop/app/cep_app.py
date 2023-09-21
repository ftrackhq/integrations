# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack
import logging

from ftrack_framework_photoshop.app.base import BasePhotoshopApplication

logger = logging.getLogger(__name__)


class CEPPhotoshopApplication(BasePhotoshopApplication):
    ''' Photoshop standalone background application for legacy CEP framework.'''

    def _connect(self):
        '''(Override)'''

        self._spawn_event_listener()

        if not self.use_uxp():
            logger.info(
                "Waiting for Photoshop {} to dial in...".format(
                    self.photoshop_version
                )
            )
