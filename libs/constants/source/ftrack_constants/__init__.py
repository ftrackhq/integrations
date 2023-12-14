# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack.
import os
import logging

from ftrack_constants import framework
from ftrack_constants import qt
from ftrack_constants import status


# Evaluate and log package version
try:
    from ftrack_utils.version import get_version

    __version__ = get_version(
        os.path.basename(os.path.dirname(__file__)),
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    )
except Exception:
    __version__ = '0.0.0'

logger = logging.getLogger(__name__)
logger.debug('v{}'.format(__version__))
