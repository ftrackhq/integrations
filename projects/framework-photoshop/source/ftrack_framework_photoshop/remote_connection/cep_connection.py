# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack
import logging

from ftrack_framework_photoshop.remote_connection.base import (
    BasePhotoshopRemoteConnection,
)

logger = logging.getLogger(__name__)


class CEPBasePhotoshopRemoteConnection(BasePhotoshopRemoteConnection):
    '''Photoshop remote connection legacy CEP framework.'''

    def connect(self):
        '''(Override)'''

        logger.info(
            "Waiting for Photoshop {} to dial in...".format(
                self.photoshop_version
            )
        )
