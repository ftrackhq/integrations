# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack

from ._version import __version__

from ftrack_connect_pipeline import constants
from ftrack_connect_pipeline.configure_logging import configure_logging

configure_logging(__name__)
from ftrack_connect_pipeline.constants.asset import *
