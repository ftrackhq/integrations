# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

import os

# Evaluate version
try:
    from ftrack_utils.version import get_version

    __version__ = get_version(
        os.path.basename(os.path.dirname(__file__)),
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    )
except Exception:
    __version__ = '0.0.0'


# DO NOT REMOVE UNUSED IMPORT - important to keep this in order to have resources
# initialised properly for applying style and providing images & fonts.
from ftrack_qt_style import (
    resource,
)

# TODO: review all the code inside this library, we should standarize docstrings.
