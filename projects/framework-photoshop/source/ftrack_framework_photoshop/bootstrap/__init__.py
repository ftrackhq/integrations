# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

import os
import logging

from ftrack_framework_core.configure_logging import configure_logging


configure_logging(
    'ftrack_connect_pipeline_photoshop',
    extra_modules=['ftrack_connect_pipeline', 'ftrack_connect_pipeline_qt'],
    propagate=False,
)


logger = logging.getLogger('ftrack_connect_pipeline_photoshop.bootstrap')

logger.info('Initializing Photoshop Framework POC')

photoshop_session_id = os.environ.get('FTRACK_INTEGRATION_SESSION_ID')
assert (
    photoshop_session_id
), 'Photoshop integration requires a FTRACK_INTEGRATION_SESSION_ID passed as environment variable!'

photoshop_version = os.environ.get('FTRACK_PHOTOSHOP_VERSION')
assert (
    photoshop_version
), 'Photoshop integration requires FTRACK_PHOTOSHOP_VERSION passed as environment variable!'

# TODO: Spawn standalone QApplication
raise Exception('Photoshop CEP integration not implemented yet!')
