# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

import os
import logging

# Evaluate version and log package version
try:
    from ftrack_utils.version import get_version

    __version__ = get_version(
        os.path.basename(os.path.dirname(__file__)),
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    )
except Exception:
    __version__ = "0.0.0"

logger = logging.getLogger(__name__)
logger.debug("v{}".format(__version__))

# DO NOT REMOVE UNUSED IMPORT - important to keep this in order to have resources
# initialised properly for applying style and providing images & fonts.
try:
    from ftrack_qt_style import (
        resource,
    )
except Exception:
    logger.exception(
        "Styling resource file not found, please install ftrack-qt-style library"
    )

# TODO: review all the code inside this library, we should standardized docstrings.
