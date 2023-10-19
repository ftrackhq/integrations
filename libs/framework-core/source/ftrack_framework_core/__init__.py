# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack.
import logging

from ._version import __version__

from ftrack_framework_core.configure_logging import configure_logging

configure_logging(__name__)
