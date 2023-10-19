# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack.
import os

from ftrack_framework_core.configure_logging import configure_logging

# Evaluate version
try:
    from ftrack_utils.version import get_version

    __version__ = get_version(
        os.path.basename(os.path.dirname(__file__)),
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    )
except Exception:
    __version__ = '0.0.0'

configure_logging(__name__)
